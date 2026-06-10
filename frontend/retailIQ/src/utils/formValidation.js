export function validateField(value, rules) {
  if (!rules) return null;
  const str = value == null ? "" : String(value).trim();
  if (rules.required && str.length === 0) {
    return rules.requiredMsg || "This field is required.";
  }
  if (str.length === 0) return null;
  if (rules.minLength != null && str.length < rules.minLength) {
    return `Must be at least ${rules.minLength} characters.`;
  }
  if (rules.maxLength != null && str.length > rules.maxLength) {
    return `Must be at most ${rules.maxLength} characters.`;
  }
  if (rules.email) {
    const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRe.test(str)) {
      return "Enter a valid email address.";
    }
  }
  if (rules.greaterThan != null) {
    const num = parseFloat(str);
    if (isNaN(num) || num <= rules.greaterThan) {
      return `Must be greater than ${rules.greaterThan}.`;
    }
  }
  if (rules.min != null && rules.greaterThan == null) {
    const num = parseFloat(str);
    if (isNaN(num) || num < rules.min) {
      return `Must be ${rules.min} or greater.`;
    }
  }
  if (rules.integer) {
    if (!/^-?\d+$/.test(str)) {
      return "Must be a whole number.";
    }
  }
  if (rules.pattern && !rules.pattern.test(str)) {
    return rules.patternMsg || "Invalid format.";
  }
  return null;
}

export function validateForm(formData, rulesMap) {
  const errors = {};
  for (const [field, rules] of Object.entries(rulesMap)) {
    const error = validateField(formData[field], rules);
    if (error) errors[field] = error;
  }
  return errors;
}

export function hasErrors(errors) {
  return Object.keys(errors).length > 0;
}

export const BUSINESS_RULES = {
  name: {
    required: true,
    requiredMsg: "Business name is required.",
    maxLength: 255,
  },
  gst_number: { maxLength: 30 },
  phone: { maxLength: 20 },
  email: { maxLength: 255, email: true },
  address: {},
  city: { maxLength: 100 },
  state: { maxLength: 100 },
  country: { maxLength: 100 },
  postal_code: { maxLength: 20 },
  logo_url: {},
  invoice_prefix: { maxLength: 20 },
  currency: { maxLength: 10 },
  timezone: { maxLength: 100 },
};

export const PRODUCT_ADD_RULES = {
  name: {
    required: true,
    requiredMsg: "Product name is required.",
    minLength: 2,
    maxLength: 50,
  },
  original_price: {
    required: true,
    requiredMsg: "MRP is required.",
    greaterThan: 0,
  },
  selling_price: {
    required: true,
    requiredMsg: "Selling price is required.",
    greaterThan: 0,
  },
  stock: {
    required: true,
    requiredMsg: "Stock quantity is required.",
    min: 0,
    integer: true,
  },
  category: { minLength: 2, maxLength: 100 },
  sku: { maxLength: 50 },
  barcode: { maxLength: 100 },
  description: { maxLength: 500 },
};

export const PRODUCT_EDIT_RULES = {
  name: {
    required: true,
    requiredMsg: "Product name is required.",
    minLength: 2,
    maxLength: 50,
  },
  original_price: {
    required: true,
    requiredMsg: "MRP is required.",
    greaterThan: 0,
  },
  selling_price: {
    required: true,
    requiredMsg: "Selling price is required.",
    greaterThan: 0,
  },
  stock: {
    required: true,
    requiredMsg: "Stock quantity is required.",
    min: 0,
    integer: true,
  },
  category: { minLength: 2, maxLength: 100 },
  sku: { maxLength: 50 },
  barcode: { maxLength: 100 },
  description: { maxLength: 500 },
};
