(() => {
  const names = ['operations_pulse','delivery_flow','crew_presence','geographic_operations','reporting_outcomes','fleet_readiness'];
  const required = ['schema_version','data_state','metrics','interpretation'];
  function override(state, data){
    if(!state) return data;
    return Object.fromEntries(Object.entries(data).map(([key,value]) => [key,{...value,data_state:state}]));
  }
  async function load(){
    const params = new URLSearchParams(location.search);
    const state = params.get('state');
    const api = window.SKYLARK_API_BASE;
    if(api){
      const responses = await Promise.all(names.map(async name => {
        const res = await fetch(`${api.replace(/\/$/,'')}/api/public/wallboard/${name}`, {headers:{Accept:'application/json'}});
        if(!res.ok) throw new Error(`projection unavailable: ${name}`);
        return [name, await res.json()];
      }));
      const projections = Object.fromEntries(responses);
      if(Object.values(projections).some(p => required.some(k => !(k in p)))) throw new Error('invalid projection envelope');
      return {synthetic:false,period:{label:'MONTH TO DATE',timezone:'IST'},snapshot_updated_at:null,projections:override(state,projections)};
    }
    const res = await fetch('data/wallboard-fixture.json');
    if(!res.ok) throw new Error('fixture unavailable');
    const fixture = await res.json();
    return {...fixture,projections:override(state,fixture.projections)};
  }
  window.WallboardData = {load};
})();