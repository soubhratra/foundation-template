'use strict';

try {
  const yaml = require('js-yaml');

  if (yaml && yaml.types && yaml.types.merge) {
    return;
  }

  const loadType = (type) => require(`js-yaml/lib/type/${type}.js`);

  yaml.types = {
    binary: loadType('binary'),
    merge: loadType('merge'),
    omap: loadType('omap'),
    pairs: loadType('pairs'),
    set: loadType('set'),
  };
} catch (error) {
  console.warn('[js-yaml-types-shim] Failed to polyfill js-yaml types:', error);
}
