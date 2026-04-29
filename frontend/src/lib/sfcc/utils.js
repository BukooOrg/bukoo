export const formatPrice = (amount, currencyCode = 'GBP') => {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: currencyCode,
  }).format(amount);
};

export const reshapeCategory = (category) => {
  if (!category) return null;
  return {
    id: category.id,
    handle: category.handle || category.id,
    title: category.title || category.name,
    description: category.description,
    seo: {
      title: category.pageTitle || category.title || category.name,
      description: category.pageDescription || category.description
    },
    parentCategoryTree: category.parentCategoryTree || []
  };
};

export const reshapeCategories = (categories) => {
  return categories.map(reshapeCategory).filter(Boolean);
};

export const reshapeProduct = (product) => {
  if (!product) return null;

  // Handle both SFCC SDK format and our simplified JSON format
  return {
    id: product.id,
    handle: product.handle || product.id,
    title: product.title || product.name,
    description: product.description || product.shortDescription || product.longDescription,
    descriptionHtml: product.descriptionHtml || product.longDescription || product.shortDescription,
    vendor: product.vendor || "Bukoo Editions",
    featuredImage: product.featuredImage || (product.imageGroups?.[0]?.images?.[0] ? {
      url: product.imageGroups[0].images[0].link,
      width: 800,
      height: 1200,
      altText: product.name
    } : null),
    priceRange: product.priceRange || {
      minVariantPrice: {
        amount: (product.price || product.min_price || "0").toString(),
        currencyCode: product.currency || product.currency_code || "GBP"
      },
      maxVariantPrice: {
        amount: (product.price || product.max_price || "0").toString(),
        currencyCode: product.currency || product.currency_code || "GBP"
      }
    },
    variants: product.variants || [],
    options: product.options || product.variationAttributes || [],
    tags: product.tags || []
  };
};

export const reshapeProducts = (products) => {
  return products.map(reshapeProduct).filter(Boolean);
};
