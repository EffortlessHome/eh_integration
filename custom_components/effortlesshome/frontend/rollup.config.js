import nodeResolve from 'rollup-plugin-node-resolve';
import typescript from 'rollup-plugin-typescript2';
import babel from 'rollup-plugin-babel';
import json from '@rollup/plugin-json';
import { terser } from 'rollup-plugin-terser';
import commonjs from '@rollup/plugin-commonjs';

const plugins = [
  nodeResolve(),
  commonjs({
    include: 'node_modules/**'
  }),
  typescript(),
  json(),
  babel({
    exclude: 'node_modules/**',
  }),
  terser()
];

terser({
  ecma: 2015,  // Specify the ECMAScript version
  compress: {
    defaults: false,  // Custom compression settings (optional)
  },
  mangle: true,  // Enable mangling
  output: {
    beautify: false,
  },
})

export default [
  {
    input: 'src/alarm-panel.ts',
    output: {
      dir: 'dist',
      format: 'iife',
      sourcemap: false
    },
    plugins: [...plugins],
    context: 'window'
  },
];