import { generateChart } from './lib/ziwei/algorithm';
import type { BirthInfo } from './lib/ziwei/types';
const input = JSON.parse(process.argv[2] ?? '{}') as BirthInfo;
const chart = generateChart(input);
process.stdout.write(JSON.stringify({birthInfo:chart.birthInfo,lunarInfo:chart.lunarInfo,mingGongBranch:chart.mingGongBranch,shenGongBranch:chart.shenGongBranch,wuxingJuName:chart.wuxingJuName,mingZhu:chart.mingZhu,shenZhu:chart.shenZhu,palaces:chart.palaces.map(p=>({name:p.name,branch:p.branch,stem:p.stem,isMingGong:p.isMingGong,isShenGong:p.isShenGong,isEmpty:p.isEmpty,borrowedStars:p.borrowedStars??[],stars:p.stars.map(s=>({name:s.name,type:s.type,brightness:s.brightnessRaw,siHua:s.siHua}))}))}));
