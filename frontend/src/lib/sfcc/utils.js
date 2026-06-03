export const formatPrice = (amount, currencyCode = 'MYR') => {
  return new Intl.NumberFormat('ms-MY', {
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
      description: category.pageDescription || category.description,
    },
    parentCategoryTree: category.parentCategoryTree || [],
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
    vendor: product.vendor || 'Bukoo Editions',
    featuredImage:
      product.featuredImage ||
      (product.imageGroups?.[0]?.images?.[0]
        ? {
            url: product.imageGroups[0].images[0].link,
            width: 800,
            height: 1200,
            altText: product.name,
          }
        : null),
    priceRange: product.priceRange || {
      minVariantPrice: {
        amount: (product.price || product.min_price || '0').toString(),
        currencyCode: product.currency || product.currency_code || 'GBP',
      },
      maxVariantPrice: {
        amount: (product.price || product.max_price || '0').toString(),
        currencyCode: product.currency || product.currency_code || 'GBP',
      },
    },
    variants: product.variants || [],
    options: product.options || product.variationAttributes || [],
    tags: product.tags || [],
  };
};

export const reshapeProducts = (products) => {
  return products.map(reshapeProduct).filter(Boolean);
};

export const fromApiBook = (book) => {
  if (!book) return null;
  const price = book.price || '0';
  const coverUrl = book.coverUrl;
  const vendor = book.publisher?.name || book.authors?.[0]?.name || 'Bukoo Editions';

  return {
    id: book.id,
    handle: book.id,
    title: book.title,
    description: book.description || '',
    descriptionHtml: book.description ? `<p>${book.description.replace(/\n/g, '</p><p>')}</p>` : '',
    vendor,
    isbn: book.isbn || null,
    pageCount: book.pageCount || null,
    language: book.language || null,
    publishedDate: book.publishedDate || null,
    publisher: book.publisher || null,
    authors: book.authors || [],
    isActive: book.isActive ?? true,
    stockQuantity: book.stockQuantity ?? 0,
    featuredImage: {
      url: coverUrl || '',
      altText: book.title,
      width: 800,
      height: 1200,
    },
    images: coverUrl ? [{ url: coverUrl, altText: book.title, width: 800, height: 1200 }] : [],
    priceRange: {
      minVariantPrice: { amount: price, currencyCode: 'MYR' },
      maxVariantPrice: { amount: price, currencyCode: 'MYR' },
    },
    variants: [],
    options: [],
    tags: [book.category?.name, ...(book.authors || []).map((a) => a.name)].filter(Boolean),
    categoryId: book.category?.id,
    availableForSale: (book.stockQuantity ?? 0) > 0,
  };
};

export const fromApiBooks = (books) => {
  return books.map(fromApiBook).filter(Boolean);
};

export const fromApiCollection = (collection) => {
  if (!collection) return null;
  return {
    id: collection.id,
    handle: collection.urlSlug || collection.id,
    title: collection.name,
    description: '',
    seo: { title: collection.name, description: '' },
    parentCategoryTree: [],
  };
};

export const fromApiCollections = (collections) => {
  return collections.map(fromApiCollection).filter(Boolean);
};

/**
 * Sort products so that items with cover images appear first.
 * Use as: products.sort(sortProductsByCover)
 */
export const sortProductsByCover = (a, b) => {
  if (a.featuredImage?.url && !b.featuredImage?.url) return -1;
  if (!a.featuredImage?.url && b.featuredImage?.url) return 1;
  return 0;
};
