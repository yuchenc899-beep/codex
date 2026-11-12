import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd();
const current=new Set(['quant-system-business.md','quant-system-technical.md','quant-system-design.md','quant-system-implementation.md','2026-11-11-quant-system-detailed-design.md']);
const files=['README.md','docs/README.md','docs/user-guide.md','docs/deployment.md','docs/changelog.md','docs/skills-and-runtime.md','docs/archive/README.md',...Array.from(current,n=>'docs/plans/'+n),...fs.readdirSync('docs/design').filter(n=>n.endsWith('.md')).map(n=>'docs/design/'+n)];
const broken=[];let count=0;
for(const file of files){const body=fs.readFileSync(file,'utf8');for(const m of body.matchAll(/\]\(([^)]+)\)/g)){const link=m[1];if(/^(https?:|#)/.test(link))continue;count++;if(!fs.existsSync(path.resolve(path.dirname(file),link.split('#')[0])))broken.push({file,link});}}
const originals=fs.readdirSync('docs/archive/2026-11-12-before-consolidation/plans').length+fs.readdirSync('docs/archive/2026-11-12-before-consolidation/design').length;
console.log(JSON.stringify({currentDocuments:files.length,localLinksChecked:count,archivedOriginals:originals,broken},null,2));if(broken.length)process.exitCode=1;

