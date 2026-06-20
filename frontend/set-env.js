const fs = require('fs');
const path = require('path');

const targetPath = path.join(__dirname, 'src/environments/environment.prod.ts');

// Read the API_URL from the environment or use a default placeholder
const apiUrl = process.env.API_URL || 'https://your-backend-railway-url.com/api';

const envConfigFile = `export const environment = {
  production: true,
  apiUrl: '${apiUrl}'
};
`;

fs.writeFile(targetPath, envConfigFile, function (err) {
  if (err) {
    console.error(err);
    throw err;
  } else {
    console.log(`Angular environment.prod.ts generated correctly with API_URL: ${apiUrl}`);
  }
});
