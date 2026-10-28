import { chromeLauncher } from '@web/test-runner-chrome';

export default {
  rootDir: '.',
  nodeResolve: true,
  browsers: [chromeLauncher({
    launchOptions: {
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    },
  })],
};
