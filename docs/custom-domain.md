# Custom domain handoff

The repository cannot safely choose a custom domain without the domain owner’s value and DNS access. Once the domain is confirmed:

1. Add the domain in GitHub Pages repository settings.
2. Create the DNS records GitHub provides, typically an apex A/ALIAS record and a `www` CNAME.
3. Enable HTTPS after DNS propagation.
4. Replace the GitHub Pages base URL in `index.html`, `design-preview.html`, `sitemap.xml`, `robots.txt`, JSON-LD, Open Graph, and Twitter metadata.
5. Update the OAuth authorized origin and callback to the final HTTPS domain.
6. Verify the custom domain, redirects, canonical tags, sitemap, robots file, favicon, 404 page, and browser console in Chromium.

Do not add a `CNAME` file until the exact domain is confirmed, because an invented value can break the current deployment.
