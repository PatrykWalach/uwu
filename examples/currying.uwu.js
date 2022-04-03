const id = (id) => {
  return id;
};
const unit = undefined;
const abs = Math.abs;
const add = (a) => (b) => {
  return a + b;
};
const multiply = (a) => (b) => {
  return a * b;
};
const to_upper = (s) => {
  return s.toUpperCase();
};
const classy_greeting = (first_name) => (last_name) => {
  return "The name's " + last_name + ", " + first_name + " " + last_name;
};
const compose1 = (f) => (g) => (a) => {
  return f(g(a));
};
const compose2 = (f) => (g) => (a) => (b) => {
  return f(g(a)(b));
};
const yell_greetings = compose2(to_upper)(classy_greeting);
yell_greetings("James")("Bond");
compose1(compose1(abs)(add(1.0)))(multiply(2.0))(-4.0);
