"""Site configuration.

Edit these values before deploying. Everything else in the build reads
from here, so the domain is never hard-coded anywhere else.
"""

# Displayed in the header, page titles, and the RSS feed.
SITE_NAME = "Alex Castro"

# Absolute URL of the deployed site, WITHOUT a trailing slash.
# Used for canonical URLs, Open Graph tags, the RSS feed, and the sitemap.
SITE_URL = "https://aic5.ai"

SITE_DESCRIPTION = "Notes on software, finance, and whatever else seems worth writing down."

AUTHOR_NAME = "Alex Castro"

# Shown in the footer copyright line.
COPYRIGHT_HOLDER = "Blue Hill Foundry LLC"

# Optional custom domain for GitHub Pages. If set (e.g. "blog.example.com"),
# the build writes a CNAME file into dist/ so GitHub Pages keeps the domain
# configured across deployments. Leave as None if you are not using a
# custom domain yet.
CUSTOM_DOMAIN = "aic5.ai"

# Number of articles shown on the homepage and included in the RSS feed.
HOMEPAGE_POST_COUNT = 10
FEED_POST_COUNT = 20

# Optional analytics snippet injected verbatim at the end of every page's
# <body>. Keep it empty for a zero-JavaScript site. If you want basic,
# privacy-friendly reader stats and view counts without running a server,
# a lightweight option is GoatCounter (https://www.goatcounter.com):
#   ANALYTICS_HTML = '<script data-goatcounter="https://YOURCODE.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
ANALYTICS_HTML = (
    '<script data-goatcounter="https://aic5.goatcounter.com/count" '
    'async src="//gc.zgo.at/count.js"></script>'
)
