import assert from 'node:assert/strict';
import {DatabaseSync} from 'node:sqlite';
import fs from 'node:fs';
import worker from '../worker/index.mjs';

class D1Statement {
  constructor(database,sql){this.database=database;this.sql=sql;this.params=[];}
  bind(...params){this.params=params;return this;}
  first(){return Promise.resolve(this.database.prepare(this.sql).get(...this.params)||null);}
  all(){return Promise.resolve({results:this.database.prepare(this.sql).all(...this.params)});}
  run(){const result=this.database.prepare(this.sql).run(...this.params);return Promise.resolve({meta:{changes:Number(result.changes)}});}
}
class TestD1 {
  constructor(){this.sqlite=new DatabaseSync(':memory:');this.sqlite.exec('PRAGMA foreign_keys=ON');for(const file of fs.readdirSync(new URL('../drizzle/',import.meta.url)).filter(n=>n.endsWith('.sql')).sort())this.sqlite.exec(fs.readFileSync(new URL('../drizzle/'+file,import.meta.url),'utf8').replaceAll('--> statement-breakpoint',''));}
  prepare(sql){return new D1Statement(this.sqlite,sql);}
  async batch(statements){return Promise.all(statements.map(statement=>statement.run()));}
}
const DB=new TestD1();
const env={DB,LEAGUE_POLL_MEMBERS:JSON.stringify([
  {name:'Joe',email:'joe@example.test',franchise_id:'van-cortlant-rangers',commissioner:true},
  {name:'Coles',email:'coles@example.test',franchise_id:'vegas-vandals'}
]),ASSETS:{fetch:()=>new Response('asset')}};
const headers=(id,email,body=false)=>({'oai-authenticated-user-id':id,'oai-authenticated-user-email':email,...(body?{'content-type':'application/json',origin:'https://rtg.test'}:{})});
async function call(path,{method='GET',id='joe-auth',email='joe@example.test',body,runtimeEnv=env}={}){
  const response=await worker.fetch(new Request('https://rtg.test'+path,{method,headers:headers(id,email,body!==undefined),body:body===undefined?undefined:JSON.stringify(body)}),runtimeEnv);
  return {status:response.status,data:await response.json()};
}
const now=Date.now(),future=now+3600000,past=now-3600000;

let result=await call('/api/account');assert.equal(result.status,200);assert.equal(result.data.approved,true);assert.equal(result.data.role,'commissioner');assert.equal('privateEmail' in result.data,false);
result=await call('/api/account',{id:'outsider',email:'outside@example.test'});assert.deepEqual(result.data,{authenticated:true,approved:false});

result=await call('/api/nfl/admin/config',{method:'POST',body:{season:2026,currentNflWeek:1,pickemStatus:'open',survivorStatus:'open',doublePickStartWeek:null,postWeek18Resolution:null,publicationStatus:'review'}});assert.equal(result.status,200);
result=await call('/api/nfl/admin/games',{method:'POST',body:{games:[{gameId:'w1-buf-nyj',season:2026,week:1,awayTeam:'BUF',homeTeam:'NYJ',kickoff:future,status:'scheduled'}]}});assert.equal(result.status,200);

result=await call('/api/nfl/survivor/me?season=2026&week=1',{id:'outsider',email:'outside@example.test'});assert.equal(result.status,200);assert.equal(result.data.canPick,false);assert.ok(result.data.games.length>0);
result=await call('/api/nfl/survivor/pick',{method:'POST',id:'outsider',email:'outside@example.test',body:{season:2026,week:1,selections:[{gameId:'w1-buf-nyj',team:'BUF'}]}});assert.equal(result.status,403);

result=await call('/api/nfl/pickem/pick',{method:'POST',body:{season:2026,week:1,gameId:'w1-buf-nyj',selectedTeam:'BUF'}});assert.equal(result.status,200);
result=await call('/api/nfl/pickem/week?season=2026&week=1');
const pickedGame=result.data.games.find(game=>game.gameId==='w1-buf-nyj');
assert.equal(pickedGame.myPick.selected_team,'BUF');assert.equal(pickedGame.distribution,null);
result=await call('/api/nfl/pickem/pick',{method:'POST',id:'outsider',email:'outside@example.test',body:{season:2026,week:1,gameId:'w1-buf-nyj',selectedTeam:'BUF'}});assert.equal(result.status,403);

result=await call('/api/nfl/survivor/pick',{method:'POST',body:{season:2026,week:1,selections:[{gameId:'w1-buf-nyj',team:'BUF'}]}});assert.equal(result.status,200);

await call('/api/nfl/admin/games',{method:'POST',body:{games:[{gameId:'w1-buf-nyj',season:2026,week:1,awayTeam:'BUF',homeTeam:'NYJ',kickoff:past,status:'final',awayScore:20,homeScore:20,winner:'TIE'}]}});
result=await call('/api/nfl/survivor/board?season=2026');assert.equal(result.data.entries[0].alive,false);assert.equal(result.data.entries[0].picks[0].team,'BUF');
result=await call('/api/nfl/pickem/pick',{method:'POST',body:{season:2026,week:1,gameId:'w1-buf-nyj',selectedTeam:'NYJ'}});assert.equal(result.status,409);

await call('/api/account',{id:'coles-auth',email:'coles@example.test'});
result=await call('/api/nfl/pickem/standings?season=2026');assert.equal(result.data.standings[0].rank,1);assert.equal(result.data.standings[1].rank,1);
assert.equal(result.data.standings.find(row=>row.displayName==='Joe').losses,1);assert.equal(result.data.standings.find(row=>row.displayName==='Joe').missedPicks,0);
assert.equal(result.data.standings.find(row=>row.displayName==='Coles').losses,1);assert.equal(result.data.standings.find(row=>row.displayName==='Coles').missedPicks,1);
result=await call('/api/my-road-to-glory?season=2026');assert.deepEqual({wins:result.data.pickem.wins,losses:result.data.pickem.losses},{wins:0,losses:1});
DB.sqlite.prepare("UPDATE members SET role='commissioner' WHERE member_id='coles'").run();
result=await call('/api/nfl/admin/config',{method:'POST',id:'coles-auth',email:'coles@example.test',body:{season:2026,currentNflWeek:1,pickemStatus:'open',survivorStatus:'open',publicationStatus:'review'}});assert.equal(result.status,403);
await call('/api/nfl/admin/config',{method:'POST',body:{season:2026,currentNflWeek:2,pickemStatus:'open',survivorStatus:'open',doublePickStartWeek:2,postWeek18Resolution:null,publicationStatus:'review'}});
await call('/api/nfl/admin/games',{method:'POST',body:{games:[
  {gameId:'w2-kc-lv',season:2026,week:2,awayTeam:'KC',homeTeam:'LV',kickoff:future,status:'scheduled'},
  {gameId:'w2-phi-dal',season:2026,week:2,awayTeam:'PHI',homeTeam:'DAL',kickoff:future,status:'scheduled'}
]}});
result=await call('/api/nfl/survivor/pick',{method:'POST',id:'coles-auth',email:'coles@example.test',body:{season:2026,week:2,selections:[{gameId:'w2-kc-lv',team:'KC'}]}});assert.equal(result.status,400);
result=await call('/api/nfl/survivor/pick',{method:'POST',id:'coles-auth',email:'coles@example.test',body:{season:2026,week:2,selections:[{gameId:'w2-kc-lv',team:'KC'},{gameId:'w2-phi-dal',team:'PHI'}]}});assert.equal(result.status,200);

const realFetch=globalThis.fetch;
globalThis.fetch=async()=>new Response(JSON.stringify({week:{number:3},events:[
  {id:'espn-w3',date:new Date(future).toISOString(),status:{type:{name:'STATUS_SCHEDULED',state:'pre',completed:false}},competitions:[{competitors:[
    {homeAway:'home',score:'0',team:{abbreviation:'MIA'}},{homeAway:'away',score:'0',team:{abbreviation:'NE'}}
  ]}]},
  {id:'espn-started',date:new Date(past).toISOString(),status:{type:{name:'STATUS_IN_PROGRESS',state:'in',completed:false}},competitions:[{competitors:[
    {homeAway:'home',score:'10',team:{abbreviation:'SEA'}},{homeAway:'away',score:'7',team:{abbreviation:'LAR'}}
  ]}]}
]}),{headers:{'Content-Type':'application/json'}});
try{
  const freshEnv={...env,DB:new TestD1()};freshEnv.DB.sqlite.prepare('UPDATE nfl_games SET updated_at=?').run(Date.now());
  result=await call('/api/nfl/config?season=2026',{runtimeEnv:freshEnv});assert.equal(result.status,200);assert.equal(result.data.config.current_nfl_week,1);assert.equal(result.data.config.survivor_status,'open');
  const automaticEnv={...env,DB:new TestD1()};
  result=await call('/api/nfl/config?season=2026',{runtimeEnv:automaticEnv});assert.equal(result.status,200);assert.equal(result.data.config.current_nfl_week,3);assert.equal(result.data.config.pickem_status,'open');assert.equal(result.data.config.survivor_status,'open');
  result=await call('/api/nfl/pickem/week?season=2026&week=3',{runtimeEnv:automaticEnv});assert.equal(result.data.games.length,1);assert.equal(result.data.games[0].gameId,'espn-w3');
  result=await call('/api/nfl/admin/sync',{method:'POST',body:{season:2026,week:3},runtimeEnv:automaticEnv});assert.equal(result.status,200);assert.equal(result.data.count,2);
  result=await call('/api/nfl/pickem/week?season=2026&week=3',{runtimeEnv:automaticEnv});assert.equal(result.data.games.length,1);assert.equal(result.data.games[0].gameId,'espn-w3');
  result=await call('/api/nfl/admin/sync',{method:'POST',body:{season:2026,week:3}});assert.equal(result.status,200);assert.equal(result.data.count,2);
  result=await call('/api/nfl/pickem/week?season=2026&week=3');assert.deepEqual(result.data.games.map(game=>game.gameId),['espn-started','espn-w3']);
  result=await call('/api/nfl/admin/sync',{method:'POST',id:'coles-auth',email:'coles@example.test',body:{season:2026,week:3}});assert.equal(result.status,403);
}finally{globalThis.fetch=realFetch;}

console.log('NFL worker E2E: authentication, authorization, automatic schedule sync, shared standings ranks, kickoff privacy/locking, Survivor tie elimination, and configurable double-pick rules passed.');
