import { build } from 'vite';

async function run() {
  try {
    await build();
    console.log('Build completed');
  } catch (err) {
    console.error('Build failed:', err);
    process.exit(1);
  }
}

run();
