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

#### Utilities

- [X] Command that queries SUs for each cluster in CSV format
- [X] Command that dumps database in JSON format
- [ ] Command that finds accounts which are using more than requested based on
  their proposal
- [ ] Command that shows current usage for an account
- [ ] Command that reads database from JSON format (dangerous!)

#### Conveniences

- [ ] Add current usage to `check_sus_limit` email
