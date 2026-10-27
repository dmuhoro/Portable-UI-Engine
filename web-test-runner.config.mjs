import { chromeLauncher } from '@web/test-runner-chrome';

export default {
  rootDir: '.',
  nodeResolve: true,
  browsers: [chromeLauncher({
    launchOptions: {
      executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    },
  })],
};
