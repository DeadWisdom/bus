import { parseArgs } from "util";
import { filesize } from "filesize";
import { watch } from "fs";
import { n } from "../build/ui/chunk-435d5b75460cfe48";

function build(options: { watch?: boolean, outDir: string }) {
  Bun.build({
    entrypoints: ['./ui/async.ts', './ui/index.ts', './ui/app.ts'],
    outdir: options.outDir,
    loader: {
      ".css": "file",
    },
    naming: {
      asset: '[name].[ext]'
    },
    publicPath: "/ui/",
    splitting: true,
    minify: true,
    sourcemap: 'external'
  }).then((result) => {
    if (result.success) {
      let items = result.outputs.filter(art => !art.path.endsWith('.map')).map(art => ({
        'name': '📗 ' + art.path.split('\\').slice(-1).join('/'),
        'loader': art.loader,
        'size': "\x1b[33m" + filesize(art.size) + "\x1b[0m"
      }));
      console.table(items);
      console.log("\n✔️ ", new Date(), "\n");
    } else {
      result.logs.forEach(log => console.error(log, '\n\n----\n'));
      console.log("\n❌ ", new Date(), "\n");
    }
  });
}

// Main ///
let { values, positionals } = parseArgs({
  args: Bun.argv,
  options: {
    watch: {
      type: 'boolean',
    },
    outDir: {
      type: 'string',
      default: './build/ui',
    }
  },
  strict: true,
  allowPositionals: true,
});

build(values as any);

if (values.watch) {
  process.on("SIGINT", () => {
    console.log("\n👍\n");
    watcher.close();
    process.exit(0);
  });

  let last = Date.now();
  let watcher = watch(import.meta.dir, { recursive: true }, (event, filename) => {
    let now = Date.now();
    if (now - last < 500) return;
    console.log(event, filename);
    build(values as any);
    last = now;
  });
}
