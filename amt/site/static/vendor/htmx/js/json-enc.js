htmx.defineExtension('json-enc', {
  onEvent: function (name, evt) {
    if (name === "htmx:configRequest") {
      evt.detail.headers['Content-Type'] = "application/json";
    }
  },

  encodeParameters: function (xhr, parameters, elt) {
    xhr.overrideMimeType('text/json');
    const options = this.getOptions(elt);
    return JSON.stringify(this.parseNestedParameters(parameters, options));
  },

  getOptions: function (elt) {
    const options = {
      cleanArrays: true
    };
    if (elt.getAttribute('data-json-enc-clean-arrays') === 'false') {
      options.cleanArrays = false;
    }
    return options;
  },

  parseNestedParameters: function (parameters, options) {
    const result = {};
    for (const [key, value] of Object.entries(parameters)) {
      this.parseKey(result, key, value);
    }
    if (options && options.cleanArrays) {
      this.cleanArrays(result);
    }
    return result;
  },

  parseKeyToSegments: function (key) {
    const segments = [];
    let currentSegment = '';
    let inBracket = false;

    for (let i = 0; i < key.length; i++) {
      const char = key[i];
      if (char === '[') {
        if (!inBracket) {
          if (currentSegment) {
            segments.push(currentSegment);
            currentSegment = '';
          }
          inBracket = true;
        } else {
          currentSegment += char;
        }
      } else if (char === ']') {
        if (inBracket) {
          segments.push(currentSegment);
          currentSegment = '';
          inBracket = false;
        } else {
          currentSegment += char;
        }
      } else {
        currentSegment += char;
      }
    }
    if (currentSegment) {
      segments.push(currentSegment);
    }
    return segments;
  },

  parseKey: function (result, key, value) {
    const segments = this.parseKeyToSegments(key);
    if (segments.length === 0) {
      result[key] = value;
      return;
    }
    let current = result;
    for (let i = 0; i < segments.length - 1; i++) {
      const segment = segments[i];
      if (current[segment] === undefined) {
        current[segment] = {};
      }
      current = current[segment];
    }
    current[segments[segments.length - 1]] = value;
  },

  cleanArrays: function (obj) {
    if (!obj || typeof obj !== 'object') return;
    for (const key in obj) {
      const value = obj[key];
      if (value && typeof value === 'object') {
        this.cleanArrays(value);
        const keys = Object.keys(value);
        let isArray = keys.length > 0;
        for (const k of keys) {
          if (isNaN(parseInt(k, 10))) {
            isArray = false;
            break;
          }
        }
        if (isArray) {
          const arr = [];
          for (const k of keys.sort((a, b) => parseInt(a, 10) - parseInt(b, 10))) {
            arr.push(value[k]);
          }
          obj[key] = arr;
        }
      }
    }
  }
});
