function id (id) {return id};const unit=undefined;function op1/*+*/ (a) {return b=>a+b};function add (a) {return function add (b) {return op1/*+*/(a)(b)}};console.log(add(2.0)(3.0))