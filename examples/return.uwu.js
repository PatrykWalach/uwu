function id(id) {
  return id;
}
const unit = undefined;
function add_one(x) {
  return x + 1.0;
}
function map(arr) {
  return (func) => arr.map(func);
}
function filter(arr) {
  return (func) => arr.filter(func);
}
const is_morning = false;
const message = (() => {
  if (is_morning) {
    return "Good morning!";
  }
  return "Hello!";
})();
const result = (() => {
  const arr1 = [1.0, 2.0, 3.0];
  const arr2 = map(arr1)(add_one);
  return filter(arr2)(function is_even(x) {
    return Object.is(x % 2, 0.0);
  });
})();
