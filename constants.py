#!/usr/bin/env python
import dataset

# The name you would like to display for the super cluster
super_cluster = "H2P"

# This should contain a list of clusters you want to track usage on
CLUSTERS = ["smp", "mpi", "gpu", "htc"]

# When running the tests, uncomment the test.db line
db = dataset.connect("sqlite:////ihome/crc/bank/crc_bank.db")
# db = dataset.connect("sqlite:///test.db")

# None of these need to change
proposal_table = db["proposal"]
investor_table = db["investor"]
investor_archive_table = db["investor_archive"]
proposal_archive_table = db["proposal_archive"]
date_format = "%m/%d/%y"

# What email should we use to send bot emails to PIs
send_email_from = "noreply@pitt.edu"

# The email suffix for your organization
# We assume the Description field of sacctmgr for the account contains the prefix
email_suffix = "@pitt.edu"

# An email to send when you have exceeded a proposal threshold (25%, 50%, 75%, 90%)
# The email better contain exactly four {}! Respectively filled with:
# 1. percent usage
# 2. proposal start date
# 3. account usage
# 4. investment information
notify_sus_limit_email_text = """\
<html>
<head></head>
<body>
<p>
To Whom It May Concern,<br><br>
This email has been generated automatically because your account on H2P has
exceeded {}% usage. The one year allocation started on {}. You can request a
supplemental allocation at
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

# An email to send when you are 90 days from the end of your proposal
# The email should contain three {}! Respectively filled with:
# 1. account
# 2. proposal end date
# 3. proposal start date
three_month_proposal_expiry_notification_email = """\
<html>
<head></head>
<body>
<p>
To Whom It May Concern,<br><br>
This email has been generated automatically because your proposal for account
{} on H2P will expire in 90 days on {}. The one year allocation started on {}.
If you would like to submit another proposal or request a supplemental
allocation please visit
https://crc.pitt.edu/Pitt-CRC-Allocation-Proposal-Guidelines.<br><br
Thanks,<br><br>
The CRC Proposal Bot
</p>
</body>
</html>
"""

# An email to send when the proposal has expired
# The email should contain two {}! Respectively filled with:
# 1. account
# 2. proposal start date
proposal_expires_notification_email = """\
<html>
<head></head>
<body>
<p>
To Whom It May Concern,<br><br>
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
