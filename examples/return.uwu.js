const id = (id) => {
  return id;
};
const unit = undefined;
const add_one = (x) => {
  return x + 1.0;
};
const map = (arr) => (func) => {
  return arr.map(func);
};
const filter = (arr) => (func) => {
  return arr.filter(func);
};
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
  const is_even = (x) => {
    return x % 2.0 === 0.0;
  };
  return filter(arr2)(is_even);
})();
