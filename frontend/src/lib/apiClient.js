import { AuthApi, HealthApi, UsersApi, Configuration } from '@bukoo/api-client';
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
export const healthApi = new HealthApi(configuration);
export const usersApi = new UsersApi(configuration);
