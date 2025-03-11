### 工具爬取及API调用场景表格

| 源名称 | 具体页面                                      | 使用情况                               |
| ------ | --------------------------------------------- | -------------------------------------- |
| NVD    | https://nvd.nist.gov/vuln/detail/*            | 使用爬虫。爬取时使用                   |
| Debian | https://security-tracker.debian.org/tracker/* | 使用爬虫，爬取时使用                   |
| Github | https://github.com/advisories/*               | 使用爬虫，爬取时使用                   |
|        | https://github.com/*/issue/ *                 | 使用爬虫，仅在解析Patch时使用          |
|        | https://github.com/*/commit/ *                | 使用Github官方API，仅在解析Patch时使用 |

