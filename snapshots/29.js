(()=>{Some=(value)=>({TAG:'Some',_0: value});None=()=>({TAG:'None',});True=()=>({TAG:'True',});False=()=>({TAG:'False',});id=(value)=>(()=>{return value})();partial=(fn)=>(arg)=>(()=>{return thunk=()=>(()=>{return fn(arg)})()})();partial(console.log)(0.0)(undefined)})()