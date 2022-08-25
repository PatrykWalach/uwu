const id = (id) => {
  return id;
};
const unit = undefined;
const len = (arr) => {
  return arr.length;
};
const get_head = (arr) => {
  return (() => {
    if (len(arr) < 1.0) {
      return "Empty";
    }
    const [_head, ..._rest] = arr;
    const list_head = _head;
    const rest = _rest;
    return { TAG: "Head", _0: list_head, _1: rest };
  })();
};
const merge = (a) => (b) => {
  const merge2 = merge;
  return (() => {
    const $ = { TAG: "Tuple", _0: get_head(a), _1: get_head(b) };
    if (typeof $ !== "string" && $.TAG === "Tuple") {
      if ($._0 === "Empty") {
        const _ = $._1;
        return b;
      }
      if ($._1 === "Empty") {
        const _ = $._0;
        return a;
      }
      if (typeof $._0 !== "string" && $._0.TAG === "Head") {
        if (typeof $._1 !== "string" && $._1.TAG === "Head") {
          const head_b = $._1._0;
          const rest_b = $._1._1;
          const head_a = $._0._0;
          const rest_a = $._0._1;
          return (() => {
            if (head_a < head_b) {
              return [head_a].concat(merge2(rest_a)(b));
            }
            return [head_b].concat(merge2(a)(rest_b));
          })();
        }
        throw new Error("Non-exhaustive pattern match");
      }
      throw new Error("Non-exhaustive pattern match");
    }
    throw new Error("Non-exhaustive pattern match");
  })();
};
