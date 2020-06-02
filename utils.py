from subprocess import Popen, PIPE
from shlex import split
from datetime import datetime, timedelta
from enum import Enum
from io import StringIO
import csv
from math import floor
from smtplib import SMTP
from email.message import EmailMessage
from bs4 import BeautifulSoup
from constants import CLUSTERS, proposal_table, investor_table, date_format


def run_command(cmd):
    out, err = Popen(split(cmd), stdout=PIPE, stderr=PIPE).communicate()
    return out.decode("utf-8"), err.decode("utf-8")


class Right:
    def __init__(self, value):
        self.value = value


class Left:
    def __init__(self, reason):
        self.reason = reason


def unwrap_if_right(x):
    if isinstance(x, Left):
        exit(x.reason)
    return x.value


def check_service_units_valid(args, greater_than_ten_thousand=True):
    lefts = []
    result = {}
    for clus in CLUSTERS:
        try:
            result[clus] = int(args[f"<{clus}>"])
        except ValueError:
            lefts.append(
                f"Given non-integer value `{args[f'<{clus}>']}` for cluster `{clus}`"
            )
    if lefts:
        return Left("\n".join(lefts))
    total_sus = sum(result.values())
    if greater_than_ten_thousand and total_sus < 10000:
        return Left(f"Total SUs should exceed 10000 SUs, got `{total_sus}`")
    elif total_sus <= 0:
        return Left(f"Total SUs should be greater than zero, got `{total_sus}`")
    return Right(result)


def account_and_cluster_associations_exists(account):
    missing = []
    for cluster in CLUSTERS:
        out, err = run_command(
            f"sacctmgr -n show assoc account={account} cluster={cluster} format=account,cluster"
        )
        if out.strip() == "":
            missing.append(cluster)
    if missing:
        return Left(
            f"Associations missing for account `{account}` on clusters `{','.join(missing)}`"
        )
    return Right(account)


def account_exists_in_table(table, account):
    q = table.find_one(account=account)
    if not q is None:
        return Right(q)
    else:
        return Left(f"Account `{account}` doesn't exist in the database")


def log_action(s):
    with open("logs/crc_bank.log", "a+") as f:
        f.write(f"{datetime.now()}: {s}\n")


def get_usage_for_account(account):
    raw_usage = 0
    for cluster in CLUSTERS:
        out, _ = run_command(
            f"sshare --noheader --account={account} --cluster={cluster} --format=RawUsage"
        )
        raw_usage += int(out.strip().split("\n")[1])
    return raw_usage / (60.0 * 60.0)


def find_next_notification(usage):
    members = list(PercentNotified)

    exceeded = [usage > x.to_percentage() for x in members]

    try:
        index = exceeded.index(False)
        result = PercentNotified.Zero if index == 0 else members[index - 1]
    except ValueError:
        result = PercentNotified.Hundred

    return result


class PercentNotified(Enum):
    Zero = 0
    TwentyFive = 1
    Fifty = 2
    SeventyFive = 3
    Ninety = 4
    Hundred = 5

    def succ(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) + 1
        if index >= len(members):
            return members[0]
        else:
            return members[index]

    def pred(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) - 1
        if index < 0:
            return members[5]
        else:
            return members[index]

    def to_percentage(self):
        if self == PercentNotified.Zero:
            return 0.0
        elif self == PercentNotified.TwentyFive:
            return 25.0
        elif self == PercentNotified.Fifty:
            return 50.0
        elif self == PercentNotified.SeventyFive:
            return 75.0
        elif self == PercentNotified.Ninety:
            return 90.0
        else:
            return 100.0


class ProposalType(Enum):
    Proposal = 0
    Class = 1
    Investor = 2


def parse_proposal_type(s):
    if s == "proposal":
        return Right(ProposalType.Proposal)
    elif s == "class":
        return Right(ProposalType.Class)
    else:
        return Left(f"Valid proposal types are `proposal` or `class`, not `{s}`")


def get_proposal_duration(t):
    return timedelta(days=365) if t == ProposalType.Proposal else timedelta(days=122)


def check_date_valid(d):
    try:
        date = datetime.strptime(d, "%m/%d/%y")
    except:
        return Left(f"Could not parse date (e.g. 12/01/19), got `{date}`")

    if date > date.today():
        return Left(f"Parsed `{date}`, but start dates shouldn't be in the future")

    return Right(date)


def get_raw_usage_in_hours(account, cluster):
    o, _ = run_command(f"sshare -A {account} -M {cluster} -P -a")
    # Only the second and third line are necessary, wrapped in text buffer
    sio = StringIO("\n".join(o.split("\n")[1:3]))

    # use built-in CSV reader to read header and data
    reader = csv.reader(sio, delimiter="|")
    header = next(reader)
    data = next(reader)

    # Find the index of RawUsage from the header
    raw_usage_idx = header.index("RawUsage")
    return convert_to_hours(data[raw_usage_idx])


def lock_account(account):
    _, _ = run_command(
        f"sacctmgr -i modify account where account={0} cluster=smp,gpu,mpi,htc set GrpTresRunMins=cpu=0"
    )


def unlock_account(account):
    _, _ = run_command(
        f"sacctmgr -i modify account where account={0} cluster=smp,gpu,mpi,htc set GrpTresRunMins=cpu=-1"
    )


def get_investment_status(account):
    cluster_h = "Cluster"
    total_investment_h = "Total Investment SUs"
    start_date_h = "Start Date"
    sus_per_year_h = "SUs Per Year"
    current_sus_h = "Current SUs"
    withdrawn_h = "Withdrawn SUs"

    cluster_w = 7
    total_investment_w = 20
    start_date_w = 10
    sus_per_year_w = 12
    current_sus_w = 11
    withdrawn_w = 13

    result_s = f"{cluster_h} | {total_investment_h} | {start_date_h} | {sus_per_year_h} | {current_sus_h} | {withdrawn_h}\n"

    for row in investor_table.find(account=account):
        for cluster in CLUSTERS:
            if row[cluster] != 0:
                per_year = f"per_year_{cluster}"
                current = f"current_{cluster}"
                withdrawn = f"withdrawn_{cluster}"
                result_s += f"{cluster:7} | {row[cluster]:20} | {row['start_date'].strftime(date_format)} | {row[per_year]:12} | {row[current]:11} | {row[withdrawn]:13}\n"

    return result_s


def notify_sus_limit(account):
    proposal_row = proposal_table.find_one(account=account)

    investment_s = get_investment_status(account)

    email_html = """\
<html>
<head></head>
<body>
<p>
To Whom it May Concern,<br><br>
This email has been generated automatically because your account on H2P has
exceeded {}% usage. The one year
allocation started on {}. If you have exceeded 100%
you can request a supplemental allocation, details available at
https://crc.pitt.edu/Pitt-CRC-Allocation-Proposal-Guidelines.<br><br>
Your usage is printed below:<br>
<pre>
{}
</pre>
Investment status (if applicable):<br>
<pre>
{}
</pre>
Thanks,<br><br>
The CRC Proposal Bot
</p>
</body>
</html>
"""

    email_html = email_html.format(
        PercentNotified(proposal_row["percent_notified"]).to_percentage(),
        proposal_row["start_date"].strftime(date_format),
        "TODO",
        investment_s,
    )

    send_email(email_html, account)


def send_email(email_html, account):
    # Extract the text from the email
    soup = BeautifulSoup(email_html, "html.parser")
    email_text = soup.get_text()

    msg = EmailMessage()
    msg.set_content(email_text)
    msg.add_alternative(email_html, subtype="html")
    msg["Subject"] = f"Your allocation on H2P for account: {account}"
    msg["From"] = "noreply@pitt.edu"
    # TODO: Need to send this to the correct email!
    msg["To"] = "bmooreii@pitt.edu"

    with SMTP("localhost") as s:
        s.send_message(msg)


def three_month_proposal_expiry_notification(account):
    proposal_row = proposal_table.find_one(account=account)

    email_html = """\
<html>
<head></head>
<body>
<p>
To Whom it May Concern,<br><br>
This email has been generated automatically because your proposal for account
{} on H2P will expire in 90 days on {}. The one year allocation started on {}.
If you would like to submit another proposal please visit
https://crc.pitt.edu/Pitt-CRC-Allocation-Proposal-Guidelines.<br><br>
Thanks,<br><br>
The CRC Proposal Bot
</p>
</body>
</html>
"""

    email_html = email_html.format(
        account,
        proposal_row["end_date"].strftime(date_format),
        proposal_row["start_date"].strftime(date_format),
    )

    send_email(email_html, account)


def proposal_expires_notification(account):
    proposal_row = proposal_table.find_one(account=account)

    email_html = """\
<html>
<head></head>
<body>
<p>
To Whom it May Concern,<br><br>
This email has been generated automatically because your proposal for account
{} on H2P has expired. The one year allocation started on {}.  If you would
like to submit another proposal please visit
https://crc.pitt.edu/Pitt-CRC-Allocation-Proposal-Guidelines.<br><br>
Thanks,<br><br>
The CRC Proposal Bot
</p>
</body>
</html>
"""

    email_html = email_html.format(
        account,
        proposal_row["end_date"].strftime(date_format),
        proposal_row["start_date"].strftime(date_format),
    )

    send_email(email_html, account)


def get_available_investor_sus(account):
    res = []
    ods = investor_table.find(account=account)
    for od in ods:
        d = {c: 0 for c in CLUSTERS}
        for c in CLUSTERS:
            d[c] += od[c] - od[f"withdrawn_{c}"]
        res.append(d)
    return res


def get_current_investor_sus(account):
    res = []
    ods = investor_table.find(account=account)
    for od in ods:
        d = {c: 0 for c in CLUSTERS}
        for c in CLUSTERS:
            d[c] += od[f"current_{c}"]
        res.append(d)
    return res


def sum_investments(investments):
    sum_d = {c: 0 for c in CLUSTERS}
    for row in investments:
        for c in CLUSTERS:
            sum_d[c] += row[c]

    return sum_d


def convert_to_hours(usage):
    return floor(int(usage) / (60.0 * 60.0))


def get_account_usage(account, cluster, avail_sus, output):
    o, _ = run_command(f"sshare -A {account} -M {cluster} -P -a")
    # Second line onward, required
    sio = StringIO("\n".join(o.split("\n")[1:]))

    # use built-in CSV reader to read header and data
    reader = csv.reader(sio, delimiter="|")
    header = next(reader)
    raw_usage_idx = header.index("RawUsage")
    user_idx = header.index("User")
    for idx, data in enumerate(reader):
        if idx != 0:
            user = data[user_idx]
            usage = convert_to_hours(data[raw_usage_idx])
            if avail_sus == 0:
                output.write(f"|{user:^20}|{usage:^30}|{'N/A':^30}|\n")
            else:
                output.write(
                    f"|{user:^20}|{usage:^30}|{100.0 * usage / avail_sus:^30}|\n"
                )
        else:
            total_cluster_usage = convert_to_hours(data[raw_usage_idx])

    return total_cluster_usage
