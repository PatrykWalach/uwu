(()=>{Some=(value)=>({TAG:'Some',_0: value});None=()=>({TAG:'None',});True=()=>({TAG:'True',});False=()=>({TAG:'False',});id=(value)=>(()=>{return value})();add=(a)=>(b)=>(()=>{return (a+b)})();addTwo=add(2.0);console.log(addTwo(3.0))})()