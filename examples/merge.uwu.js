const unit = undefined;
const /* < */ op6 = (a) => (b) => {
    return a < b;
  };
const /* ++ */ op9 = (a) => (b) => {
    return a.concat(b);
  };
const len = (arr) => {
  return arr.length;
};
const get_head = (arr) => {
  return (() => {
    if (op6(len(arr))(/* < */ 1.0)) {
      return "Empty";
    }
    const [_head, ..._rest] = arr;
    const list_head = _head;
    const rest = _rest;
    return { TAG: "Head", _0: list_head, _1: rest };
  })();
};
