import React, { useState, useEffect, useCallback } from "react";
import { useTheme } from "../context/ThemeContext";
import { useAppAuth } from "../context/AuthContext";
import {
  fetchLLMConfigs,
  fetchMultiAgentModels,
  saveMultiAgentModels,
  fetchSingleAgentModel,
  saveSingleAgentModel,
  saveLLMConfig,
  deleteLLMConfig,
  testLLMConnection,
  fetchPreferences,
  updatePreferences,
  fetchOllamaModels,
  fetchGitHubStatus,
  fetchGitHubRepos,
  connectGitHubApp,
  disconnectGitHub,
  fetchGitHubAuthUrl
} from "../api";

interface LLMConfig {
  id: string;
  config_name: string;
  provider: string;
  masked_key: string;
  base_url?: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  is_active: number | boolean;
}

const PROVIDER_DEFAULT_MODELS: Record<string, string> = {
  groq: "openai/gpt-oss-20b",
  openai: "gpt-4o",
  gemini: "gemini-2.5-flash",
  anthropic: "claude-3-5-sonnet-20241022",
  ollama: "llama3.2:latest"
};

const Configuration: React.FC = () => {
  const { theme, setTheme, themes } = useTheme();
  const { user, isLoaded } = useAppAuth();

  // State: Configurations & Preferences
  const [configs, setConfigs] = useState<LLMConfig[]>([]);
  const [agentMode, setAgentMode] = useState<"single" | "multi">("single");
  const [multiAgentConfigIds, setMultiAgentConfigIds] = useState<string[]>([]);
  const [savingMultiAgentModels, setSavingMultiAgentModels] = useState(false);
  const [singleAgentConfigId, setSingleAgentConfigId] = useState("");
  const [savingSingleAgentModel, setSavingSingleAgentModel] = useState(false);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<{ type: "success" | "error" | "info"; text: string } | null>(null);
  const [formNotice, setFormNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // State: Add / Edit Model Form
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingConfigId, setEditingConfigId] = useState<string | null>(null);
  const [configName, setConfigName] = useState("");
  const [provider, setProvider] = useState("groq");
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("http://localhost:11434");
  const [modelName, setModelName] = useState(PROVIDER_DEFAULT_MODELS["groq"]);
  const [temperature, setTemperature] = useState(0.1);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [testingConnection, setTestingConnection] = useState(false);

  // State: Ollama detected models
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [detectingOllama, setDetectingOllama] = useState(false);

  // State: GitHub connection
  const [githubStatus, setGithubStatus] = useState<{
    connected: boolean;
    username?: string;
    installation_id?: string;
    has_pem?: boolean;
    install_url?: string;
    app_name?: string;
    client_id?: string;
  }>({ connected: false });
  const [githubRepos, setGithubRepos] = useState<any[]>([]);
  const [connectingApp, setConnectingApp] = useState(false);
  const [ghUsernameInput, setGhUsernameInput] = useState("");
  const [linkingGh, setLinkingGh] = useState(false);
  const [refreshingGh, setRefreshingGh] = useState(false);
  const [linkError, setLinkError] = useState("");
  const [linkSuccess, setLinkSuccess] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Load LLM Configs
      const cfgRes = await fetchLLMConfigs();
      if (cfgRes.data?.success) {
        setConfigs(cfgRes.data.configs || []);
      }

      // 2. Load User Preferences
      const prefRes = await fetchPreferences();
      if (prefRes.data?.success) {
        setAgentMode(prefRes.data.preferences?.agent_mode || "single");
      }

      const multiModelRes = await fetchMultiAgentModels();
      if (multiModelRes.data?.success) {
        setMultiAgentConfigIds(multiModelRes.data.config_ids || []);
      }

      const singleModelRes = await fetchSingleAgentModel();
      if (singleModelRes.data?.success) {
        setSingleAgentConfigId(singleModelRes.data.config_id || "");
      }

      // 3. Load GitHub Status
      const ghRes = await fetchGitHubStatus();
      if (ghRes.data) {
        setGithubStatus(ghRes.data);
        if (ghRes.data.connected) {
          try {
            const rRes = await fetchGitHubRepos();
            if (rRes.data?.success && Array.isArray(rRes.data.repositories)) {
              setGithubRepos(rRes.data.repositories);
            }
          } catch (rErr) {
            console.warn("Could not load authorized repositories:", rErr);
          }
        } else {
          setGithubRepos([]);
        }
      }
    } catch (e: any) {
      console.warn("Could not load configuration data:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isLoaded) return;
    loadData();

    // Check if returning from GitHub App installation
    const params = new URLSearchParams(window.location.search);
    const instId = params.get("installation_id");
    const accountParam = params.get("account") || "";
    if (instId) {
      window.history.replaceState({}, document.title, window.location.pathname);
      connectGitHubApp({
        installation_id: instId,
        github_username: (accountParam && accountParam !== "User") ? accountParam : undefined
      }).then((res) => {
        const connectedName = res.data?.username || (accountParam !== "User" ? accountParam : "");
        setNotice({
          type: "success",
          text: `🎉 GitHub App connected successfully${connectedName ? ` as @${connectedName}` : ""}! Your repositories are now accessible.`
        });
        loadData();
      }).catch((err) => {
        console.warn("Post-install link notification:", err);
        loadData();
      });
    } else if (params.get("github_connected") === "1") {
      window.history.replaceState({}, document.title, window.location.pathname);
      const acct = params.get("account") || "";
      setNotice({
        type: "success",
        text: `🎉 GitHub App connected successfully${acct ? ` as @${acct}` : ""}! Your authorized repositories are now ready.`
      });
      loadData();
    } else if (params.get("github_error")) {
      setNotice({
        type: "error",
        text: `GitHub authorization error: ${params.get("github_error")}`
      });
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [loadData, isLoaded, user?.id]);

  // Handle Provider Change in Add Form
  const handleProviderChange = (newProv: string) => {
    setProvider(newProv);
    setModelName(PROVIDER_DEFAULT_MODELS[newProv] || "");
    if (newProv === "ollama") {
      setBaseUrl("http://localhost:11434");
      autoDetectOllama("http://localhost:11434");
    }
  };

  // Auto-Detect Ollama models
  const autoDetectOllama = async (urlToTest?: string) => {
    setDetectingOllama(true);
    try {
      const res = await fetchOllamaModels(urlToTest || baseUrl);
      if (res.data?.success && Array.isArray(res.data.models)) {
        const names = res.data.models.map((m: any) => m.name);
        setOllamaModels(names);
        if (names.length > 0 && !names.includes(modelName)) {
          setModelName(names[0]);
        }
        setNotice({ type: "success", text: `Found ${names.length} local models from Ollama!` });
      } else {
        setNotice({ type: "error", text: "Could not detect Ollama models. Is Ollama running locally?" });
      }
    } catch {
      setNotice({ type: "error", text: "Cannot reach Ollama at " + baseUrl });
    } finally {
      setDetectingOllama(false);
    }
  };

  // Test Connection
  const handleTestConnection = async () => {
    setTestingConnection(true);
    setFormNotice(null);
    setNotice(null);
    try {
      const res = await testLLMConnection({
        provider,
        model_name: modelName,
        api_key: apiKey,
        base_url: provider === "ollama" ? baseUrl : undefined
      });
      if (res.data?.success) {
        const msg = res.data.message || "Connection verified successfully!";
        setFormNotice({ type: "success", text: msg });
        setNotice({ type: "success", text: msg });
      } else {
        const msg = res.data?.message || "Connection verification failed.";
        setFormNotice({ type: "error", text: msg });
        setNotice({ type: "error", text: msg });
      }
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || "Failed to reach model provider. Please check credentials or URL.";
      setFormNotice({ type: "error", text: msg });
      setNotice({ type: "error", text: msg });
    } finally {
      setTestingConnection(false);
    }
  };

  // Save Model Config
  const handleSaveModel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!configName.trim() || !modelName.trim()) {
      setNotice({ type: "error", text: "Please provide a configuration name and model." });
      return;
    }

    try {
      const res = await saveLLMConfig({
        ...(editingConfigId ? { id: editingConfigId } : {}),
        config_name: configName.trim(),
        provider,
        api_key: apiKey.trim(),
        base_url: provider === "ollama" ? baseUrl.trim() : null,
        model_name: modelName.trim(),
        temperature,
        max_tokens: maxTokens,
        is_active: editingConfigId
          ? Boolean(configs.find((config) => config.id === editingConfigId)?.is_active)
          : configs.length === 0
      });

      if (res.data?.success) {
        setNotice({ type: "success", text: `Configuration "${configName}" ${editingConfigId ? "updated" : "saved"} successfully!` });
        setShowAddForm(false);
        setEditingConfigId(null);
        setConfigName("");
        setApiKey("");
        setFormNotice(null);
        await loadData();
      }
    } catch (e: any) {
      setNotice({ type: "error", text: e.response?.data?.detail || "Could not save configuration." });
    }
  };

  const resetModelForm = () => {
    setEditingConfigId(null);
    setConfigName("");
    setProvider("groq");
    setApiKey("");
    setBaseUrl("http://localhost:11434");
    setModelName(PROVIDER_DEFAULT_MODELS.groq);
    setTemperature(0.1);
    setMaxTokens(4096);
    setFormNotice(null);
  };

  const handleEditModel = (config: LLMConfig) => {
    setEditingConfigId(config.id);
    setConfigName(config.config_name);
    setProvider(config.provider);
    setApiKey("");
    setBaseUrl(config.base_url || "http://localhost:11434");
    setModelName(config.model_name);
    setTemperature(config.temperature);
    setMaxTokens(config.max_tokens);
    setFormNotice(null);
    setShowAddForm(true);
  };

  // Delete Model
  const handleDelete = async (id: string) => {
    if (!window.confirm("Are you sure you want to delete this configuration?")) return;
    try {
      await deleteLLMConfig(id);
      await loadData();
      setNotice({ type: "success", text: "Configuration deleted." });
    } catch (e: any) {
      setNotice({ type: "error", text: "Failed to delete configuration." });
    }
  };

  // Update Review Mode
  const handleModeChange = async (mode: "single" | "multi") => {
    setAgentMode(mode);
    try {
      await updatePreferences({ agent_mode: mode });
      setNotice({ type: "success", text: `Review mode set to: ${mode === "multi" ? "Multi-Agent" : "Single Agent"}` });
    } catch (e: any) {
      console.warn("Failed to save mode preference:", e);
    }
  };

  const handleMultiAgentModelToggle = async (configId: string) => {
    const nextIds = multiAgentConfigIds.includes(configId)
      ? multiAgentConfigIds.filter((id) => id !== configId)
      : [...multiAgentConfigIds, configId];
    setSavingMultiAgentModels(true);
    try {
      const response = await saveMultiAgentModels(nextIds);
      setMultiAgentConfigIds(response.data?.config_ids || nextIds);
      setNotice({ type: "success", text: "Multi-agent model pool saved." });
    } catch (error: any) {
      setNotice({ type: "error", text: error.response?.data?.detail || "Could not save the multi-agent model pool." });
    } finally {
      setSavingMultiAgentModels(false);
    }
  };

  const handleSingleAgentModelSelect = async (configId: string) => {
    setSavingSingleAgentModel(true);
    try {
      const response = await saveSingleAgentModel(configId);
      setSingleAgentConfigId(response.data?.config_id || configId);
      setNotice({ type: "success", text: "Single-agent model saved." });
    } catch (error: any) {
      setNotice({ type: "error", text: error.response?.data?.detail || "Could not save the single-agent model." });
    } finally {
      setSavingSingleAgentModel(false);
    }
  };

  // GitHub Connect via App (1-click using detected installation)
  const handleConnectGitHubApp = async (instId?: string) => {
    try {
      setConnectingApp(true);
      const res = await connectGitHubApp(instId);
      if (res.data?.success) {
        setNotice({ type: "success", text: res.data.message || "Connected via GitHub App!" });
        await loadData();
      }
    } catch (e: any) {
      setNotice({ type: "error", text: e.response?.data?.detail || "Failed to link via GitHub App." });
    } finally {
      setConnectingApp(false);
    }
  };

  const handleDisconnectGitHub = async () => {
    if (!window.confirm("Disconnect GitHub account?")) return;
    try {
      await disconnectGitHub();
      await loadData();
      setNotice({ type: "success", text: "GitHub account disconnected." });
    } catch (e: any) {
      setNotice({ type: "error", text: "Failed to disconnect." });
    }
  };

  const handleLinkUsername = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanUsername = ghUsernameInput.trim().replace(/^@/, "");
    if (!cleanUsername) return;

    setLinkingGh(true);
    setLinkError("");
    setLinkSuccess("");
    try {
      const res = await connectGitHubApp({ github_username: cleanUsername });
      if (res.data?.success) {
        setLinkSuccess(`Successfully connected as @${res.data.username || cleanUsername}! Loading repositories...`);
        setNotice({
          type: "success",
          text: `🎉 GitHub account @${res.data.username || cleanUsername} successfully connected!`
        });
        setGhUsernameInput("");
        await loadData();
      } else {
        setLinkError(res.data?.message || "Could not link account.");
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.response?.data?.message || err.message || "Could not verify GitHub App installation for this username.";
      setLinkError(msg);
    } finally {
      setLinkingGh(false);
    }
  };

  const handleRefreshStatus = async () => {
    setRefreshingGh(true);
    setLinkError("");
    try {
      const res = await fetchGitHubStatus();
      if (res.data?.connected) {
        setNotice({
          type: "success",
          text: `✓ Connected as @${res.data.username}!`
        });
        await loadData();
      } else {
        // Attempt an auto-connect check across active installations
        try {
          const autoRes = await connectGitHubApp({});
          if (autoRes.data?.success) {
            setNotice({
              type: "success",
              text: `🎉 Auto-detected and connected as @${autoRes.data.username}!`
            });
            await loadData();
            return;
          }
        } catch {}
        await loadData();
        setNotice({
          type: "info",
          text: "App not linked yet. If you installed the GitHub App on your account, enter your GitHub username below to link instantly!"
        });
      }
    } catch {
      setNotice({
        type: "error",
        text: "Could not refresh GitHub connection status."
      });
    } finally {
      setRefreshingGh(false);
    }
  };

  return (
    <main className="config-container">
      <div className="config-header">
        <h1>⚙️ Workspace Configuration</h1>
        <p>Configure AI review models, multi-agent workflows, theme aesthetics, and GitHub integrations.</p>
      </div>

      {notice && (
        <div className={`alert alert-${notice.type}`} style={{ marginBottom: "20px" }}>
          {notice.text}
        </div>
      )}

      {/* SECTION 1: LLM PROVIDERS & MODELS */}
      <section className="config-section">
        <div className="config-section-header">
          <div className="config-section-title">
            <span>🧠</span>
            <div>
              <h3>AI Models & Providers</h3>
              <p style={{ fontSize: "14px", color: "var(--text-secondary)", fontWeight: 400, marginTop: "2px" }}>
                Add, edit, or remove cloud API keys and local Ollama configurations.
              </p>
            </div>
          </div>
          <button
            type="button"
            className="btn-primary"
            onClick={() => {
              if (showAddForm) {
                setShowAddForm(false);
                resetModelForm();
              } else {
                resetModelForm();
                setShowAddForm(true);
              }
            }}
          >
            {showAddForm ? "Cancel" : "+ Add New Model"}
          </button>
        </div>

        {/* ADD MODEL FORM */}
        {showAddForm && (
          <form onSubmit={handleSaveModel} style={{ backgroundColor: "var(--bg-subtle)", padding: "24px", borderRadius: "var(--radius-lg)", marginBottom: "24px", border: "1px solid var(--border)" }}>
            <h4 style={{ marginBottom: "16px", fontSize: "17px" }}>{editingConfigId ? "Edit AI Model Configuration" : "Add New AI Model Configuration"}</h4>

            <div className="form-grid">
              <div className="form-group">
                <label>Configuration Name</label>
                <input
                  type="text"
                  placeholder="e.g. My Llama 3.2 or Fast Groq"
                  value={configName}
                  onChange={(e) => setConfigName(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Provider</label>
                <select value={provider} onChange={(e) => handleProviderChange(e.target.value)}>
                  <option value="groq">Groq Cloud (Fast & Free Tier)</option>
                  <option value="openai">OpenAI (GPT-4o, GPT-4o-mini)</option>
                  <option value="gemini">Google Gemini (Gemini 2.5)</option>
                  <option value="anthropic">Anthropic Claude (Claude 3.5 Sonnet)</option>
                  <option value="ollama">Ollama (100% Local / Free)</option>
                </select>
              </div>

              {provider === "ollama" ? (
                <>
                  <div className="form-group">
                    <label>Ollama Server URL</label>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <input
                        type="text"
                        value={baseUrl}
                        onChange={(e) => setBaseUrl(e.target.value)}
                        placeholder="http://localhost:11434"
                        style={{ flex: 1 }}
                      />
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={() => autoDetectOllama(baseUrl)}
                        disabled={detectingOllama}
                      >
                        {detectingOllama ? "Scanning..." : "Detect"}
                      </button>
                    </div>
                  </div>

                  <div className="form-group">
                    <label>Local Model Name</label>
                    {ollamaModels.length > 0 ? (
                      <select value={modelName} onChange={(e) => setModelName(e.target.value)}>
                        {ollamaModels.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={modelName}
                        onChange={(e) => setModelName(e.target.value)}
                        placeholder="llama3.2:latest, codellama, etc."
                      />
                    )}
                  </div>
                </>
              ) : (
                <>
                  <div className="form-group">
                    <label>API Key</label>
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder={provider === "groq" ? "gsk_..." : "sk-..."}
                    />
                  </div>

                  <div className="form-group">
                    <label>Model ID</label>
                    <input
                      type="text"
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                      placeholder={PROVIDER_DEFAULT_MODELS[provider]}
                      required
                    />
                  </div>
                </>
              )}

              <div className="form-group">
                <label>Temperature ({temperature})</label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label>Max Completion Tokens ({maxTokens})</label>
                <input
                  type="range"
                  min="1024"
                  max="8192"
                  step="512"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                />
              </div>
            </div>

            {formNotice && (
              <div
                style={{
                  marginTop: "16px",
                  padding: "12px 16px",
                  borderRadius: "8px",
                  fontSize: "14px",
                  fontWeight: 600,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: "10px",
                  background: formNotice.type === "success" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                  color: formNotice.type === "success" ? "#059669" : "#dc2626",
                  border: `1px solid ${formNotice.type === "success" ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)"}`
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "16px" }}>{formNotice.type === "success" ? "✅" : "⚠️"}</span>
                  <span>{formNotice.text}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setFormNotice(null)}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", fontSize: "16px", padding: "2px 6px" }}
                >
                  ✕
                </button>
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "20px" }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleTestConnection}
                disabled={testingConnection}
                style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}
              >
                {testingConnection ? (
                  <>
                    <span className="review-spinner-small" /> Verifying Connection...
                  </>
                ) : (
                  "⚡ Test Connection"
                )}
              </button>
              <button type="submit" className="btn-primary">
                {editingConfigId ? "Update Model Configuration" : "Save Model Configuration"}
              </button>
            </div>
          </form>
        )}

        {/* CONFIGURED MODELS LIST */}
        <div className="config-models-list">
          {configs.length === 0 ? (
            <div style={{ textAlign: "center", padding: "30px", color: "var(--text-muted)" }}>
              <p style={{ marginBottom: "12px" }}>No custom models configured yet.</p>
              <span style={{ fontSize: "14px" }}>The application is currently utilizing the default high-speed cloud Groq model. Click "+ Add New Model" above to configure your OpenAI, Claude, Gemini, or Ollama local models!</span>
            </div>
          ) : (
            configs.map((c) => {
              return (
                <div key={c.id} className="model-config-card">
                  <div className="model-info-main">
                    <span className="model-provider-badge">{c.provider}</span>
                    <div>
                      <div className="model-name-label">{c.config_name}</div>
                      <div className="model-sub-label">
                        Model: <code>{c.model_name}</code> • Temp: {c.temperature} {c.masked_key ? `• Key: ${c.masked_key}` : ""} {c.base_url ? `• ${c.base_url}` : ""}
                      </div>
                    </div>
                  </div>

                  <div className="model-card-actions">
                    <button type="button" className="btn-secondary" style={{ padding: "6px 12px", fontSize: "13px" }} onClick={() => handleEditModel(c)}>Edit</button>

                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: "6px 12px", fontSize: "13px", color: "var(--danger)" }}
                      onClick={() => handleDelete(c.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>

      {/* SECTION 2: SINGLE VS MULTI-AGENT REVIEW MODE */}
      <section className="config-section">
        <div className="config-section-header">
          <div className="config-section-title">
            <span>🤖</span>
            <div>
              <h3>Review Execution Mode</h3>
              <p style={{ fontSize: "14px", color: "var(--text-secondary)", fontWeight: 400, marginTop: "2px" }}>
                Choose between fast single-agent processing or deep multi-agent collaborative audits.
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
          <div
            onClick={() => handleModeChange("single")}
            style={{
              padding: "20px",
              borderRadius: "var(--radius-lg)",
              border: `2px solid ${agentMode === "single" ? "var(--primary)" : "var(--border)"}`,
              backgroundColor: agentMode === "single" ? "var(--primary-light)" : "var(--bg-card)",
              cursor: "pointer",
              transition: "var(--transition)"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <strong style={{ fontSize: "16px", color: "var(--text-primary)" }}>⚡ Single Agent Mode</strong>
              {agentMode === "single" && <span className="badge-active">Selected</span>}
            </div>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
              Executes unified RAG retrieval in a single pass. Fast, cost-efficient, and ideal for quick reviews.
            </p>
          </div>

          <div
            onClick={() => handleModeChange("multi")}
            style={{
              padding: "20px",
              borderRadius: "var(--radius-lg)",
              border: `2px solid ${agentMode === "multi" ? "var(--primary)" : "var(--border)"}`,
              backgroundColor: agentMode === "multi" ? "var(--primary-light)" : "var(--bg-card)",
              cursor: "pointer",
              transition: "var(--transition)"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <strong style={{ fontSize: "16px", color: "var(--text-primary)" }}>🛡️ Multi-Agent Collaborative Mode</strong>
              {agentMode === "multi" && <span className="badge-active">Selected</span>}
            </div>
            <p style={{ fontSize: "14px", color: "var(--text-secondary)", margin: 0, lineHeight: 1.5 }}>
              Spawns 4 specialized parallel reviewers (Bug Detective, Security Auditor, Performance Architect, Clean Code Inspector) merged by a Synthesis Agent. Maximum audit depth.
            </p>
          </div>
        </div>

        <div style={{ marginTop: "22px", padding: "20px", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", background: "var(--bg-card)" }}>
          <h4 style={{ margin: "0 0 6px", color: "var(--text-primary)" }}>Single-Agent Model</h4>
          <p style={{ margin: "0 0 14px", color: "var(--text-secondary)", fontSize: "14px", lineHeight: 1.5 }}>
            Choose the one saved model used for single-agent reviews. This choice is separate from the multi-agent model pool.
          </p>
          {configs.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: "14px" }}>Add a model configuration above to choose a single-agent model. Until then, the server uses its default model.</div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
              {configs.map((config) => {
                const checked = singleAgentConfigId === config.id;
                return (
                  <label key={config.id} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "12px", border: `1px solid ${checked ? "var(--primary)" : "var(--border)"}`, borderRadius: "var(--radius-md)", cursor: savingSingleAgentModel ? "wait" : "pointer", opacity: savingSingleAgentModel ? 0.7 : 1 }}>
                    <input
                      type="radio"
                      name="single-agent-model"
                      checked={checked}
                      disabled={savingSingleAgentModel}
                      onChange={() => void handleSingleAgentModelSelect(config.id)}
                    />
                    <span style={{ minWidth: 0 }}>
                      <strong style={{ display: "block", color: "var(--text-primary)" }}>{config.config_name}</strong>
                      <small style={{ color: "var(--text-secondary)" }}>{config.provider} · {config.model_name}</small>
                    </span>
                  </label>
                );
              })}
            </div>
          )}
        </div>

        <div style={{ marginTop: "16px", padding: "20px", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", background: "var(--bg-card)" }}>
          <h4 style={{ margin: "0 0 6px", color: "var(--text-primary)" }}>Multi-Agent Model Pool</h4>
          <p style={{ margin: "0 0 14px", color: "var(--text-secondary)", fontSize: "14px", lineHeight: 1.5 }}>
            Choose one or more saved models. Each multi-agent review randomly assigns a model from this pool to each specialist and the synthesis step. This selection is independent from the single-agent model.
          </p>
          {configs.length === 0 ? (
            <div style={{ color: "var(--text-muted)", fontSize: "14px" }}>Add a model configuration above to build your multi-agent pool.</div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "10px" }}>
              {configs.map((config) => {
                const checked = multiAgentConfigIds.includes(config.id);
                return (
                  <label key={config.id} style={{ display: "flex", alignItems: "center", gap: "10px", padding: "12px", border: `1px solid ${checked ? "var(--primary)" : "var(--border)"}`, borderRadius: "var(--radius-md)", cursor: savingMultiAgentModels ? "wait" : "pointer", opacity: savingMultiAgentModels ? 0.7 : 1 }}>
                    <input
                      type="checkbox"
                      checked={checked}
                      disabled={savingMultiAgentModels}
                      onChange={() => void handleMultiAgentModelToggle(config.id)}
                    />
                    <span style={{ minWidth: 0 }}>
                      <strong style={{ display: "block", color: "var(--text-primary)" }}>{config.config_name}</strong>
                      <small style={{ color: "var(--text-secondary)" }}>{config.provider} · {config.model_name}</small>
                    </span>
                  </label>
                );
              })}
            </div>
          )}
          <div style={{ marginTop: "12px", color: "var(--text-muted)", fontSize: "13px" }}>
            {multiAgentConfigIds.length === 0
              ? "No models selected; multi-agent reviews will use the selected single-agent model."
              : `${multiAgentConfigIds.length} model${multiAgentConfigIds.length === 1 ? "" : "s"} selected for multi-agent reviews.`}
          </div>
        </div>
      </section>

      {/* SECTION 3: WORKSPACE THEMES */}
      <section className="config-section">
        <div className="config-section-header">
          <div className="config-section-title">
            <span>🎨</span>
            <div>
              <h3>Workspace Appearance</h3>
              <p style={{ fontSize: "14px", color: "var(--text-secondary)", fontWeight: 400, marginTop: "2px" }}>
                Select your preferred visual aesthetic. Saves immediately to your profile and across browser sessions.
              </p>
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px" }}>
          {themes.map((t) => {
            const isSelected = theme === t.id;
            return (
              <div
                key={t.id}
                onClick={() => setTheme(t.id)}
                style={{
                  padding: "16px",
                  borderRadius: "var(--radius-lg)",
                  border: `2px solid ${isSelected ? "var(--primary)" : "var(--border)"}`,
                  backgroundColor: "var(--bg-card)",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  transition: "var(--transition)",
                  boxShadow: isSelected ? "var(--shadow-md)" : "none"
                }}
              >
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "50%",
                    backgroundColor: t.primaryColor,
                    boxShadow: `0 0 8px ${t.primaryColor}88`
                  }}
                />
                <div>
                  <strong style={{ fontSize: "15px", display: "block" }}>{t.name}</strong>
                  <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>{t.subtitle}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* SECTION 4: GITHUB APP INTEGRATION */}
      <section className="config-section">
        <div className="config-section-header">
          <div className="config-section-title">
            <span>🔗</span>
            <div>
              <h3>GitHub App Integration</h3>
              <p style={{ fontSize: "14px", color: "var(--text-secondary)", fontWeight: 400, marginTop: "2px" }}>
                Connect GitHub to pull repositories, run multi-agent reviews, preview proposed code diffs, and push Pull Requests.
              </p>
            </div>
          </div>
          {githubStatus.connected && (
            <button type="button" className="btn-secondary" onClick={handleDisconnectGitHub}>
              Disconnect
            </button>
          )}
        </div>

        {githubStatus.connected ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "16px 20px",
              backgroundColor: "var(--success-bg)",
              border: "1px solid var(--success-border)",
              borderRadius: "var(--radius-md)",
              flexWrap: "wrap",
              gap: "12px"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span style={{ fontSize: "24px" }}>✅</span>
                <div>
                  <strong style={{ color: "var(--success)", fontSize: "15px" }}>Connected to GitHub as @{githubStatus.username}</strong>
                  <div style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "2px" }}>
                    GitHub App authorization active. Ready to audit repositories, inspect diffs, and create automated PRs.
                  </div>
                </div>
              </div>
              <div style={{ display: "flex", gap: "10px" }}>
                <a
                  href="https://github.com/settings/installations"
                  target="_blank"
                  rel="noreferrer"
                  className="btn-secondary"
                  style={{ textDecoration: "none", fontSize: "13px", display: "inline-flex", alignItems: "center", gap: "6px" }}
                >
                  Manage on GitHub ↗
                </a>
                <button type="button" className="btn-secondary" onClick={handleDisconnectGitHub} style={{ fontSize: "13px" }}>
                  Disconnect
                </button>
              </div>
            </div>

            {/* Authorized Repositories */}
            {githubRepos && githubRepos.length > 0 && (
              <div style={{ backgroundColor: "var(--bg-subtle)", padding: "16px 20px", borderRadius: "var(--radius-md)", border: "1px solid var(--border)" }}>
                <div style={{ fontSize: "12.5px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "12px" }}>
                  Authorized Repositories ({githubRepos.length})
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "10px" }}>
                  {githubRepos.map((repo: any) => (
                    <div
                      key={repo.id}
                      style={{
                        padding: "12px 14px",
                        background: "var(--bg-card)",
                        border: "1px solid var(--border)",
                        borderRadius: "var(--radius-sm)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between"
                      }}
                    >
                      <div style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        <a
                          href={repo.html_url}
                          target="_blank"
                          rel="noreferrer"
                          style={{ fontWeight: 600, fontSize: "13.5px", color: "var(--primary)", textDecoration: "none" }}
                        >
                          {repo.full_name}
                        </a>
                        <div style={{ fontSize: "11.5px", color: "var(--text-muted)", marginTop: "3px" }}>
                          Branch: <code>{repo.default_branch || "main"}</code> {repo.private ? "• Private" : "• Public"}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            padding: "24px",
            maxWidth: "680px"
          }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: "16px", marginBottom: "18px" }}>
              <span style={{ fontSize: "32px", lineHeight: 1 }}>🐙</span>
              <div>
                <h4 style={{ margin: "0 0 6px 0", fontSize: "16px" }}>Connect via Official GitHub App</h4>
                <p style={{ margin: 0, fontSize: "13.5px", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  Authorize the GitHub App to grant the AI assistant access to your repositories. No manual personal access token is required—install once on your account or organization and pick which repositories you want reviewed.
                </p>
              </div>
            </div>

            <div style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "10px",
              marginBottom: "20px",
              padding: "12px 16px",
              background: "var(--bg-subtle)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border)"
            }}>
              <span style={{ fontSize: "12.5px", color: "var(--text-secondary)", display: "inline-flex", alignItems: "center", gap: "5px" }}>
                ✓ No Personal Access Tokens
              </span>
              <span style={{ fontSize: "12.5px", color: "var(--text-secondary)", display: "inline-flex", alignItems: "center", gap: "5px" }}>
                ✓ Granular Repository Control
              </span>
              <span style={{ fontSize: "12.5px", color: "var(--text-secondary)", display: "inline-flex", alignItems: "center", gap: "5px" }}>
                ✓ Automated Diff Review & PR Creation
              </span>
            </div>

            <div style={{ display: "flex", gap: "14px", alignItems: "center", flexWrap: "wrap", marginBottom: "20px" }}>
              <a
                href={githubStatus.install_url || "https://github.com/apps/code-review-assistant-project/installations/new"}
                target="_self"
                className="btn-primary"
                style={{
                  textDecoration: "none",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "10px 22px",
                  fontSize: "14px",
                  fontWeight: 600
                }}
              >
                <span>⚡</span>
                <span>Install GitHub App ↗</span>
              </a>

              <button
                type="button"
                className="btn-secondary"
                onClick={handleRefreshStatus}
                disabled={refreshingGh}
                style={{ fontSize: "13px", display: "inline-flex", alignItems: "center", gap: "6px", padding: "9px 16px" }}
              >
                <span>{refreshingGh ? "⏳" : "🔄"}</span> {refreshingGh ? "Checking GitHub..." : "Refresh Status"}
              </button>

              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                Redirects to GitHub to grant repository access
              </span>
            </div>

            {/* Instant Link Card for users who already installed the app */}
            <div style={{
              background: "var(--bg-subtle)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius-md)",
              padding: "18px 20px"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                <span style={{ fontSize: "20px" }}>🔗</span>
                <div>
                  <strong style={{ fontSize: "14px", color: "var(--text-main)" }}>
                    Already installed the GitHub App on your account?
                  </strong>
                  <div style={{ fontSize: "12.5px", color: "var(--text-secondary)", marginTop: "2px" }}>
                    Enter your GitHub username to link your installation and load your repositories immediately:
                  </div>
                </div>
              </div>

              <form onSubmit={handleLinkUsername} style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap", marginTop: "12px" }}>
                <div style={{
                  display: "inline-flex",
                  alignItems: "center",
                  background: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: "var(--radius-sm)",
                  padding: "0 12px",
                  minWidth: "260px"
                }}>
                  <span style={{ color: "var(--text-muted)", fontSize: "14px", fontWeight: 600, marginRight: "4px" }}>@</span>
                  <input
                    type="text"
                    value={ghUsernameInput}
                    onChange={(e) => setGhUsernameInput(e.target.value)}
                    placeholder="e.g. reddy-sidhardha24"
                    style={{
                      background: "transparent",
                      border: "none",
                      outline: "none",
                      color: "var(--text-main)",
                      fontSize: "13.5px",
                      padding: "9px 0",
                      width: "100%"
                    }}
                  />
                </div>

                <button
                  type="submit"
                  className="btn-primary"
                  disabled={linkingGh || !ghUsernameInput.trim()}
                  style={{
                    padding: "9px 20px",
                    fontSize: "13.5px",
                    fontWeight: 600,
                    cursor: linkingGh || !ghUsernameInput.trim() ? "not-allowed" : "pointer"
                  }}
                >
                  {linkingGh ? "Verifying..." : "Connect My Account"}
                </button>
              </form>

              {linkError && (
                <div style={{ marginTop: "12px", padding: "8px 12px", background: "var(--danger-bg)", border: "1px solid var(--danger-border, rgba(239, 68, 68, 0.3))", borderRadius: "6px", color: "var(--danger)", fontSize: "12.5px" }}>
                  ⚠️ {linkError}
                </div>
              )}
              {linkSuccess && (
                <div style={{ marginTop: "12px", padding: "8px 12px", background: "var(--success-bg)", border: "1px solid var(--success-border, rgba(16, 185, 129, 0.3))", borderRadius: "6px", color: "var(--success)", fontSize: "12.5px" }}>
                  ✓ {linkSuccess}
                </div>
              )}
            </div>
          </div>
        )}
      </section>
    </main>
  );
};

export default Configuration;
