const unit=undefined;const op1/*+*/=(a)=>(b)=>{return a+b};const add=(a)=>{const add=(b)=>{return op1/*+*/(a)(b)};return add};console.log(add(2.0)(3.0))