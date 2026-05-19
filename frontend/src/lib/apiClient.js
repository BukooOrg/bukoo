import {
  AuthApi,
  AuthorApi,
  HealthApi,
  UserApi,
  CategoryApi,
  Configuration,
  CollectionApi,
  BookApi,
  CartApi,
  WishlistApi,
  OrderApi,
  PublisherApi,
  ReviewApi,
  NotificationApi,
} from '@bukoo/api-client';
import Cookies from 'js-cookie';

const configuration = new Configuration({
  basePath: '',
  middleware: [
    {
      pre: async (context) => {
        const token = Cookies.get('jwt');
        if (token) {
          context.init.headers = {
            ...context.init.headers,
            Authorization: `Bearer ${token}`,
          };
        }
        return context;
      },
    },
  ],
});

export const authApi = new AuthApi(configuration);
export const authorApi = new AuthorApi(configuration);
export const bookApi = new BookApi(configuration);
export const cartApi = new CartApi(configuration);
export const categoryApi = new CategoryApi(configuration);
export const collectionApi = new CollectionApi(configuration);
export const healthApi = new HealthApi(configuration);
export const notificationApi = new NotificationApi(configuration);
export const orderApi = new OrderApi(configuration);
export const publisherApi = new PublisherApi(configuration);
export const reviewApi = new ReviewApi(configuration);
export const userApi = new UserApi(configuration);
export const wishlistApi = new WishlistApi(configuration);
