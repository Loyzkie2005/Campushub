# CampusHub

Campus marketplace, facilities booking and specialized service workflows for USTP Oroquieta. BSIT capstone and research project, 2026.

The system uses Django for web administration and application business rules, Flutter for mobile, PostgreSQL for records, and FastAPI for messaging only.

## Start here

| What you need | Document |
| --- | --- |
| Whole-project purpose, plan, architecture, module map and data flow | [CampusHub System Overview](docs/campushub-system-overview.md) |
| Engineering rules and verified institutional workflows | [AGENTS.md](AGENTS.md) |
| Latest accepted decisions and implementation history | [CAMPUSHUB_CONTEXT.md](CAMPUSHUB_CONTEXT.md) |
| Product audience, goals and boundaries | [PRODUCT.md](PRODUCT.md) |
| Backend folder layout and where code belongs | [Backend architecture](backend/core/modules/ARCHITECTURE.md) |
| Web UI/UX rules | [Web design guide](docs/web-ui-ux-guidelines.md) |
| Current mobile fonts and exceptions | [Mobile typography](docs/mobile-typography.md) |
| Mobile design reference | [DESIGN.md](https://github.com/Loyzkie2005/CampusHub-Mobile/blob/main/DESIGN.md) |
| Mobile entry points and development checks | [Flutter project README](https://github.com/Loyzkie2005/CampusHub-Mobile) |
| Debugging and feature-specific test evidence | [Debugging guide](docs/DEBUGGING_GUIDE.md) and the [feature index](docs/campushub-system-overview.md#feature-documentation-index) |
| Deployment and turnover planning | [Deployment guide](docs/kamatera-web-deployment.md), [turnover checklist](docs/system-turnover-checklist.md) |
| Chat-only service setup | [Chat README](backend/chat_service/README.md) |

## Repository structure

```text
CAMPUSHUB/
|-- backend/
|   |-- core/          Django settings, APIs, accounts and feature modules
|   |-- chat_service/  FastAPI messaging service and its own schema migrations
|   |-- templates/     Shared/admin Django templates
|   |-- static/        Web CSS, JavaScript, fonts and images
|   `-- deployment/    Deployment support files
|-- campushub/          Separate local Flutter repository (ignored by web Git)
|-- docs/              Feature guides, design rules, debugging and verification
|-- frontend/          Additional static/admin/reference material; trace usage first
|-- scratch/           Local review evidence and experiments, not runtime source
|-- AGENTS.md          Engineering instructions
|-- PRODUCT.md         Product brief
`-- CAMPUSHUB_CONTEXT.md  Latest decisions and historical context
```

The served Django web interface is assembled from its configured templates and static directories. Do not assume `frontend/` is a separate running web app. The overview explains the actual request paths and source locations.

Temporary review folders were moved out of this project on November 4, 2026 to `C:\Users\leste\Desktop\CAMPUSHUB-artifacts-20261104`. Historical `scratch/` evidence references resolve within that archive. Capture tests may recreate ignored output directories; application modules, test suites and reusable partial templates remain in their original locations. See the [cleanup report](docs/DEBUGGING_GUIDE.md#temporary-artifact-cleanup---november-4-2026).

The Flutter client is independently versioned in [CampusHub Mobile](https://github.com/Loyzkie2005/CampusHub-Mobile). The adjacent `campushub/` folder remains on this computer, but the web repository does not track it or contain a submodule. See the [repository separation guide](docs/repository-separation.md) for clone/push commands.

## Working on a feature

1. Read the engineering rules, latest relevant context entry and existing feature guide.
2. Trace the screen, service/API, permission check and business helper before editing.
3. Preserve existing workflows; put application rules in Django and chat logic in FastAPI.
4. Verify the changed behavior with appropriate isolated checks and real render evidence when layout changes.
5. Update the existing feature guide with causes, file/line anchors, data flow, actual checks and limitations.

The plan in the overview organizes work by deliverables and acceptance evidence. It is not a claim that every capstone capability has passed institutional acceptance or is deployed. Follow the deployment guide for environment-specific setup; this README does not authorize migrations, production writes or deployment.
