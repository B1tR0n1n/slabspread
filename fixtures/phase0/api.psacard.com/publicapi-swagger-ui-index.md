---
url: https://api.psacard.com/publicapi/swagger/ui/index
fetched_at: 2026-09-26T00:24:35Z
status: 200 VERIFIED-BY-FETCH (curl) - Swagger UI shell HTML (loads /publicapi/swagger.json)
---

<!-- HTML for static distribution bundle build -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="SwaggerIU" />
    <title>Swagger UI</title>
    <link
      rel="stylesheet"
      href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css"
    />
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script
      src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"
      crossorigin
    ></script>
    <script
      src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"
      crossorigin
    ></script>
    <script>
      const disableTryItOutPlugin = function () {
        return {
          statePlugins: {
            spec: {
              wrapSelectors: {
                allowTryItOutFor: function () {
                  return function () {
                    return true;
                  };
                },
              },
            },
          },
        };
      };

      window.onload = () => {
        window.ui = SwaggerUIBundle({
          url: '/publicapi/swagger.json',
          validatorUrl: null,
          docExpansion: 'none',
          operationsSorter: 'none',
          defaultModelsExpandDepth: 1,
          defaultModelExpandDepth: 1,
          tagsSorter: 'none',
          dom_id: '#swagger-ui',
          deepLinking: true,
          presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
          plugins: [SwaggerUIBundle.plugins.DownloadUrl, disableTryItOutPlugin],
          layout: 'StandaloneLayout',
        });
      };
    </script>
  <script>(function(){function c(){var b=a.contentDocument||(a.contentWindow&&a.contentWindow.document);if(b){var d=b.createElement('script');d.innerHTML="window.__CF$cv$params={r:'a40e13debb6f289e',t:'MTc5MDM4MTc2Mg=='};var a=document.createElement('script');a.src='/cdn-cgi/challenge-platform/scripts/jsd/main.js';document.getElementsByTagName('head')[0].appendChild(a);";b.getElementsByTagName('head')[0].appendChild(d)}}if(document.body){var a=document.createElement('iframe');a.height=1;a.width=1;a.style.position='absolute';a.style.top=0;a.style.left=0;a.style.border='none';a.style.visibility='hidden';document.body.appendChild(a);if('loading'!==document.readyState)c();else if(window.addEventListener)document.addEventListener('DOMContentLoaded',c);else{var e=document.onreadystatechange||function(){};document.onreadystatechange=function(b){e(b);'loading'!==document.readyState&&(document.onreadystatechange=e,c())}}}})();</script></body>
</html>

