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


def check_service_units_valid(args, clusters, greater_than_ten_thousand=True):
    lefts = []
    result = {}
    for clus in clusters:
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


def account_and_cluster_associations_exists(account, clusters):
    missing = []
    for cluster in clusters:
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
    with open("logs/crc-bank.log", "a+") as f:
        f.write(f"{datetime.now()}: {s}\n")


def get_usage_for_account(account, clusters):
    raw_usage = 0
    for cluster in clusters:
        out, _ = run_command(
            f"sshare --noheader --account={account} --cluster={cluster} --format=RawUsage"
        )
        raw_usage += int(out.strip().split("\n")[1])
    return raw_usage / (60.0 * 60.0)


class PercentNotified(Enum):
    Zero = 0
    TwentyFive = 1
    Fifty = 2
    SeventyFive = 3
    Ninety = 4
    Hundred = 5


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
    o, _ = run_command(f"sshare -A {account} -M {cluster} -P")
    # Only the second and third line are necessary, wrapped in text buffer
    sio = StringIO("\n".join(o.split("\n")[1:3]))

    # use built-in CSV reader to read header and data
    reader = csv.reader(sio, delimiter="|")
    header = next(reader)
    data = next(reader)

    # Find the index of RawUsage from the header
    raw_usage_idx = header.index("RawUsage")
    return floor(int(data[raw_usage_idx]) / (60.0 * 60))


def lock_account(account):
    _, _ = run_command(
        f"sacctmgr -i modify account where account={0} cluster=smp,gpu,mpi,htc set GrpTresRunMins=cpu=0"
    )


def unlock_account(account):
    _, _ = run_command(
        f"sacctmgr -i modify account where account={0} cluster=smp,gpu,mpi,htc set GrpTresRunMins=cpu=-1"
    )


# TODO: Need to pass the proposal information and get the usage inside this function
def notify_sus_limit(account):
    email_html = f"""\
<html>
<head></head>
<body>
<p>
To Whom it May Concern,<br><br>
This email has been generated automatically because your account on H2P has
been locked. The one year allocation started on TODO. You'll need to submit
another proposal requesting a supplemental allocation, details available
https://crc.pitt.edu/Pitt-CRC-Allocation-Proposal-Guidelines.<br><br>
Your usage is printed below:<br>
<pre>
TODO
</pre>
Thanks,<br><br>
The CRC Proposal Bot
</p>
</body>
</html>
"""

    # Extract the text from the email
    soup = BeautifulSoup(email_html, "html.parser")
    email_text = soup.get_text()

    msg = EmailMessage()
    msg.set_content(email_text)
    # msg.add_alternative(email_html, subtype="html")
    msg["Subject"] = f"Your allocation on H2P for account: {account}"
    msg["From"] = "noreply@pitt.edu"
    msg["To"] = "bmooreii@pitt.edu"

    with SMTP("localhost") as s:
        s.send_message(msg)
