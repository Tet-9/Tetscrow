const TetApi = (() => {
  function authHeaders() {
    const jwt = localStorage.getItem("tet_jwt");
    return jwt ? { Authorization: `Bearer ${jwt}` } : {};
  }

  async function request(path, options = {}) {
    const res = await fetch(`${window.TET_CONFIG.API_BASE}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...authHeaders(), ...(options.headers || {}) },
    });
    if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
    return res.status === 204 ? null : res.json();
  }

  return {
    myEscrows: () => request("/escrows/mine"),
    getEscrow: (id, sync = false) => request(`/escrows/${id}${sync ? "?sync=true" : ""}`),
    createEscrow: (body) => request("/escrows", { method: "POST", body: JSON.stringify(body) }),
    confirmEscrow: (id, body) => request(`/escrows/${id}/confirm`, { method: "POST", body: JSON.stringify(body) }),
    raiseDispute: (body) => request("/disputes", { method: "POST", body: JSON.stringify(body) }),
    getDisputes: (escrowId) => request(`/disputes/${escrowId}`),
    tokenStats: () => request("/token/stats"),
  };
})();
