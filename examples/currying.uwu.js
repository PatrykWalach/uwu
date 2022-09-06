function id(id) {
  return id;
}
const unit = undefined;
function op1 /*+*/(a) {
  return (b) => a + b;
}
function op2 /*/*/(a) {
  return (b) => Math.floor(a / b);
}
function op3 /***/(a) {
  return (b) => a * b;
}
function op4 /****/(a) {
  return (b) => a ** b;
}
function op5 /*-*/(a) {
  return (b) => a - b;
}
function op6 /*<*/(a) {
  return (b) => a < b;
}
function op7 /*>*/(a) {
  return (b) => a > b;
}
function op8 /*>=*/(a) {
  return (b) => a >= b;
}
function op9 /*<=*/(a) {
  return (b) => a <= b;
}
function op10 /*+.*/(a) {
  return (b) => a + b;
}
function op11 /*/.*/(a) {
  return (b) => a / b;
}
function op12 /**.*/(a) {
  return (b) => a * b;
}
function op13 /***.*/(a) {
  return (b) => a ** b;
}
function op14 /*-.*/(a) {
  return (b) => a - b;
}
function op15 /*<.*/(a) {
  return (b) => a < b;
}
function op16 /*>.*/(a) {
  return (b) => a > b;
}
function op17 /*>=.*/(a) {
  return (b) => a >= b;
}
function op18 /*<=.*/(a) {
  return (b) => a <= b;
}
function op19 /*<>*/(a) {
  return (b) => a + b;
}
function op20 /*=~*/(a) {
  return (b) => b.test(a);
}
function op21 /*==*/(a) {
  return (b) => Object.is(a, b);
}
function op22 /*!=*/(a) {
  return (b) => !Object.is(a, b);
}
function op23 /*++*/(a) {
  return (b) => a.concat(b);
}
function op24 /*&&*/(a) {
  return (b) => a && b;
}
function op25 /*and*/(a) {
  return (b) => a && b;
}
function op26 /*||*/(a) {
  return (b) => a || b;
}
function op27 /*or*/(a) {
  return (b) => a || b;
}
const abs = Math.abs;
function add(a) {
  return (b) => op1(/*+*/ a)(b);
}
function multiply(a) {
  return (b) => op3(/***/ a)(b);
}
function to_upper(s) {
  return s.toUpperCase();
}
function classy_greeting(first_name) {
  return (last_name) =>
    op19(/*<>*/ "The name's ")(
      op19(/*<>*/ last_name)(
        op19(/*<>*/ ", ")(op19(/*<>*/ first_name)(op19(/*<>*/ " ")(last_name)))
      )
    );
}
function compose1(f) {
  return (g) => (a) => f(g(a));
}
function compose2(f) {
  return (g) => (a) => (b) => f(g(a)(b));
}
const yell_greetings = compose2(to_upper)(classy_greeting);
yell_greetings("James")("Bond");
compose1(compose1(abs)(add(1.0)))(multiply(2.0))(-4.0);
