const unit = undefined;
const /* + */ op1 = (a) => (b) => {
    return a + b;
  };
const /* == */ op10 = (a) => (b) => {
    return Object.is(a, b);
  };
const add_one = (x) => {
  return op1(x)(/* + */ 1.0);
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
    return op10(x % 2)(/* == */ 0.0);
  };
  return filter(arr2)(is_even);
})();
