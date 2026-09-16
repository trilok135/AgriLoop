import { defineConfig } from 'vite';
import { resolve } from 'path';

export default defineConfig({
  root: '.',
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname, 'index.html'),
        baler: resolve(import.meta.dirname, 'frontend/stitch_agritrace_frontend_operations_suite/baler_operator_data_capture_minimal/code.html'),
        farmer: resolve(import.meta.dirname, 'frontend/stitch_agritrace_frontend_operations_suite/farmer_view_payment_status_minimal/code.html')
      }
    }
  }
});
