# Introduction to Proximity

## Welcome to Your Personal Cloud's Operating System

Proximity is more than just another container orchestration tool—it's a **complete application delivery platform** designed to transform your Proxmox VE infrastructure into a modern, user-friendly cloud environment that rivals the simplicity of platforms like Heroku, while maintaining the control and privacy of self-hosting.

---

## 🌍 The Vision

### What We're Building

We're building **the missing layer** between Proxmox VE's powerful but complex infrastructure and the applications you want to run. Proximity is designed to:

- **Abstract complexity** without hiding power
- **Prioritize user experience** without sacrificing capability
- **Default to security** without requiring expertise  
- **Enable automation** without removing control
- **Support scale** without demanding it

### Who Proximity Is For

#### 🏠 **Home Lab Enthusiasts**
Run your personal applications (Nextcloud, Plex, Home Assistant) without wrestling with Docker Compose files and reverse proxies.

#### 🚀 **Developers**
Quickly spin up development environments, test stacks, and demo applications without infrastructure overhead.

#### 🏢 **Small Teams**
Self-host team tools (GitLab, Mattermost, project management) with professional-grade deployment and backup workflows.

#### 🎓 **Learners**
Explore containerization, networking, and infrastructure concepts through an intuitive interface with real-world applications.

#### 💼 **IT Professionals**
Manage internal services with enterprise features (automated backups, monitoring, audit logs) on your own hardware.

---

## 🧭 Core Philosophy

### 1. **UX-First, Always**

> "If it takes more than 3 clicks, we've failed."

Every feature in Proximity is designed with the end-user experience as the primary concern. Technical correctness matters, but not at the expense of usability.

**In Practice:**
- **One-Click Deployment**: From browsing to running in seconds
- **In-App Canvas**: Access apps without leaving Proximity
- **Living App Cards**: Real-time metrics without separate dashboards
- **Integrated Console**: Terminal access without SSH clients

### 2. **Security by Default**

> "Users shouldn't have to be security experts to be secure."

Proximity ships with secure defaults that protect users automatically:

**Security Measures:**
- ✅ **Unprivileged LXC containers** (no root escapes)
- ✅ **JWT authentication** with role-based access control
- ✅ **Encrypted credential storage** (AES-256)
- ✅ **Network isolation** between applications
- ✅ **Audit logging** for administrative actions
- ✅ **Automatic security updates** (when enabled)

### 3. **Intelligent Automation**

> "Automate the tedious, expose the important."

Proximity features **AUTO & PRO modes** to match your workflow:

#### 🤖 AUTO Mode
**Hands-free operation** for users who want reliability without maintenance:
- Daily automated backups at 2:00 AM
- Weekly update checks every Sunday
- Automatic cleanup of stale resources
- Simplified interface focused on essentials

#### 🛠️ PRO Mode
**Full manual control** for power users who want fine-grained authority:
- On-demand backup creation
- One-click app cloning
- Live resource editing (CPU, RAM, disk)
- Advanced configuration access
- Complete feature set unlocked

**Switch anytime** based on your current needs.

### 4. **Progressive Disclosure**

> "Make simple things simple, complex things possible."

Proximity's interface reveals complexity gradually:

1. **Level 1**: Deploy apps with zero configuration
2. **Level 2**: Customize environment variables and resources
3. **Level 3**: Access container console and Docker internals
4. **Level 4**: Edit network configuration and advanced settings

New users see a clean, minimal interface. Advanced users can dive deep.

### 5. **No Vendor Lock-In**

> "Your data, your infrastructure, your rules."

Proximity is **completely open-source** (MIT License) and:
- ✅ Stores everything in **standard Proxmox LXC containers**
- ✅ Uses **vanilla Docker** (no proprietary runtime)
- ✅ Exports backups in **Proxmox vzdump format**
- ✅ Exposes a **full REST API** for automation
- ✅ Can be **self-compiled** and modified freely

**You can migrate away** from Proximity at any time—your containers will continue running.

---

## 🎯 Key Design Decisions

### Why Proxmox VE?

**Proxmox VE** provides an enterprise-grade virtualization platform that's:
- Free and open-source
- Battle-tested and stable
- Feature-rich (clustering, HA, backups, snapshots)
- Hardware-efficient (bare-metal performance)

By building on Proxmox, Proximity inherits decades of infrastructure engineering while providing a modern application layer.

### Why LXC Containers?

**LXC (Linux Containers)** offer the perfect balance:
- **Lighter than VMs**: Sub-second startup, minimal overhead
- **Stronger isolation than Docker**: Separate kernel namespaces
- **Native to Proxmox**: First-class support and management
- **Resource-efficient**: Run hundreds of containers on modest hardware

Each application gets its own **isolated LXC container** with Docker inside—combining the best of both worlds.

### Why Vanilla JavaScript?

Proximity's frontend uses **no frameworks** (React, Vue, Angular). Instead, it leverages:

- **ES6 Modules**: Native browser support, no build step needed
- **Custom Router**: Lightweight lifecycle management
- **Observer Pattern**: Reactive state without virtual DOM overhead
- **Web Components**: Reusable UI elements with encapsulation

**Benefits:**
- ⚡ **Instant load times** (no framework bundle to download)
- 🐛 **Easier debugging** (no transpilation, no sourcemaps)
- 🎓 **Lower learning curve** (standard JavaScript, no DSL)
- 🔧 **Full control** (no framework limitations)

### Why FastAPI?

**FastAPI** is Python's most modern web framework:
- Automatic OpenAPI documentation
- Type safety with Pydantic
- Native async/await support
- Exceptional performance (on par with Node.js)
- Intuitive dependency injection

Combined with **SQLAlchemy** (ORM) and **SQLite** (database), the backend is robust yet simple to deploy.

---

## 🚀 The Proximity Advantage

### Compared to Manual Proxmox Management

| Task | Manual Proxmox | Proximity |
|------|----------------|-----------|
| Deploy app | 30+ min, 15+ steps | 60 seconds, 1 click |
| Configure networking | Complex NAT/routing | Automatic with ports |
| Install Docker | Manual SSH commands | Included automatically |
| Setup backups | Cron jobs, scripts | Built-in scheduler |
| Monitor resources | Multiple tools | Integrated dashboard |
| Access console | SSH + terminal | Web-based console |
| Update app | Manual Docker pull | One-click upgrade |

### Compared to Cloudron/CasaOS

| Feature | Cloudron | CasaOS | **Proximity** |
|---------|----------|--------|---------------|
| Platform | Docker | Docker | **Proxmox LXC + Docker** |
| Isolation | Container | Container | **Container + LXC** |
| Pricing | $15-30/mo | Free | **Free (Open-Source)** |
| Backup format | Proprietary | Local | **Proxmox vzdump** |
| Network arch | Traefik | Simple | **Port-based or Appliance** |
| Auto mode | Yes | No | **Yes (AUTO mode)** |
| Pro mode | No | No | **Yes (PRO mode)** |
| API | REST | Limited | **Full REST API** |

### Compared to Heroku/Platform.sh

| Aspect | Heroku/Platform.sh | **Proximity** |
|--------|-------------------|---------------|
| Hosting | Cloud (someone else's servers) | **Your hardware** |
| Privacy | Third-party access | **Complete control** |
| Cost | $$ (per month, per app) | **Free** |
| Vendor lock-in | High (proprietary runtime) | **None (standard tech)** |
| Scale | Unlimited (pay more) | **Hardware-limited** |
| Simplicity | ⭐⭐⭐⭐⭐ | **⭐⭐⭐⭐⭐** |

---

## 🔮 The Roadmap

### Current State (v0.1.x)

✅ Core application deployment and lifecycle management  
✅ AUTO & PRO modes for flexible workflows  
✅ Integrated web console and In-App Canvas  
✅ Automated backups and update detection  
✅ Real-time monitoring and "living" app cards  
✅ Comprehensive E2E test suite (250+ tests)  

### Near-Term (v0.2.x)

🔄 **GitOps-Based Core** - Declare infrastructure as code  
🔄 **Multi-User Support** - Teams and organizations  
🔄 **App Marketplace** - Community-contributed templates  
🔄 **Advanced Networking** - Custom domains and SSL  
🔄 **Container Registry** - Private image hosting  

### Long-Term Vision

🌟 **Kubernetes Integration** - Scale beyond single-cluster  
🌟 **Multi-Cloud Support** - Manage Proxmox + AWS/Azure  
🌟 **AI-Powered Ops** - Intelligent resource optimization  
🌟 **Plugin Ecosystem** - Extend Proximity with custom features  
🌟 **Enterprise Edition** - High-availability, clustering, compliance  

---

## 🤝 Community & Contribution

Proximity is built by the community, for the community. We believe in:

- **Radical transparency**: All decisions and code are public
- **Inclusive collaboration**: Everyone's input matters
- **Quality over speed**: Ship when ready, not on deadlines
- **Documentation-first**: If it's not documented, it doesn't exist

### Ways to Contribute

1. **Use Proximity** and provide feedback
2. **Report bugs** with detailed reproduction steps
3. **Request features** with clear use cases
4. **Write documentation** for missing areas
5. **Contribute code** for features or fixes
6. **Help others** in Discussions and Issues
7. **Spread the word** if you find it useful

Every contribution—no matter how small—makes Proximity better.

---

## 📚 Next Steps

Now that you understand Proximity's philosophy and vision, explore the documentation:

- **[Deployment Guide](2_DEPLOYMENT.md)** - Install and configure Proximity
- **[Usage Guide](3_USAGE_GUIDE.md)** - Learn to use every feature
- **[Architecture Deep-Dive](4_ARCHITECTURE.md)** - Understand how it works internally
- **[Development Guide](5_DEVELOPMENT.md)** - Contribute to the project

---

<div align="center">

**Welcome to the future of self-hosted application delivery.** 🚀

[Back to README](../README.md) • [Next: Deployment Guide →](2_DEPLOYMENT.md)

</div>
