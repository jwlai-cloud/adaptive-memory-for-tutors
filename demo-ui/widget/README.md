# Embeddable Insight Feed

Drop this script into any page that can reach the demo UI host:

```html
<script
  src="http://localhost:3000/widget/insight-feed.js"
  data-tenant-id="demo-school"
  data-student-ref="demo-student-1"
  data-pair-id="kana-so-n"
></script>
```

The script creates an iframe that renders the live insight-log feed through
the same server-side backend proxy used by the full demo UI. No API key is
placed in the host page, iframe URL, or browser bundle.
