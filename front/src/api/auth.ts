import api from "./api";

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

const TOKEN_KEY = "odm_token";

export const authService = {
  async login(email: string, password: string): Promise<TokenResponse> {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const res = await api.post<TokenResponse>(
      "/auth/login",
      formData.toString(),
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );

    localStorage.setItem(TOKEN_KEY, res.access_token);
    return res;
  },

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    window.location.href = "/login";
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },

  async getCurrentUser(): Promise<User> {
    return api.get<User>("/auth/me");
  },
};

export default authService;
