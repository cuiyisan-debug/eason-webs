# Virtual Portfolio Demo

This is a fake-data test site for the `feishu-portfolio-launch` workflow.

Open `index.html` directly in a browser, or serve this folder with a static server. The page reads `api/portfolio.json`, renders a filterable portfolio grid, and includes the Feishu refresh templates needed for a future GitHub Pages deployment.

When switching to real Feishu data, configure these GitHub repository secrets:

- `LARK_APP_ID`
- `LARK_APP_SECRET`
- `LARK_BASE_TOKEN`
- `LARK_TABLE_ID`

Then run `.github/workflows/refresh.yml` to generate fresh `api/*.json` files.
