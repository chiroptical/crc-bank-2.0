TODO
---

#### Basic Usage

- [X] Implement `add` for `Proposal`/`Class`
- [X] Implement `change` for `Proposal`/`Class`
- [X] Implement `modify_date` for `Proposal`/`Class`
- [X] Implement `investor` proposal
- [X] Implement `withdraw` for investments

#### Checks

- [X] Check account has run out of SUs
- [X] Check account has passed proposal period
- [X] Check proposal will end within three months
- [X] `check_sus_limit` needs to archive exhausted investments

#### Utilities

- [X] Command that queries SUs for each cluster in CSV format
- [X] Command that dumps database in JSON format
- [X] Command that finds accounts which are using more than requested based on
  their proposal
- [X] Command that shows current usage for an account
- [ ] Command that reads database from JSON format (dangerous!)

#### Conveniences

- [X] Add current usage to `check_sus_limit` email
