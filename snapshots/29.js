;;const id=(id)=>(()=>{return id})();id;const unit=undefined;unit;const partial=(fn)=>(arg)=>(()=>{const thunk=()=>(()=>{return fn(arg)})();return thunk})();partial;partial(console.log)(0.0)(unit)
