# Embeddable Insight Feed

Drop this script into any page that can reach the demo UI host:

```html
<script
  src="http://localhost:3000/widget/insight-feed.js"
  data-api-base="http://localhost:8000"
  data-api-key="local-demo-test-key"
  data-tenant-id="demo-school"
  data-student-ref="demo-student-1"
  data-pair-id="kana-so-n"
></script>
```

The script creates an iframe that renders the live insight-log feed from the
same REST API used by the full demo UI.
