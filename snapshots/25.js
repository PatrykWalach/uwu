(()=>{Some=(value)=>({TAG:'Some',_0: value});None=()=>({TAG:'None',});True=()=>({TAG:'True',});False=()=>({TAG:'False',});id=(value)=>(()=>{return value})();add=(a)=>(()=>{return add=(b)=>(()=>{return (a+b)})()})();console.log(add(2.0)(3.0))})()