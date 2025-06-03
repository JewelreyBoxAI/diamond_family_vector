# 🛡️ Branch Protection Setup Guide

## GitHub Branch Protection Rules (Manual Setup Required)

To complete the protection of your production deployment, you need to set up branch protection rules on GitHub. This prevents direct pushes to `main` and requires Pull Request reviews.

### Step-by-Step Setup:

1. **Go to Repository Settings**
   - Navigate to: https://github.com/JewelreyBoxAI/diamond_family_vector/settings/branches

2. **Add Branch Protection Rule**
   - Click "Add rule"
   - Branch name pattern: `main`

3. **Configure Protection Settings**
   ```
   ✅ Require a pull request before merging
   ✅ Require approvals (set to 1)
   ✅ Dismiss stale PR approvals when new commits are pushed
   ✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging
   ✅ Include administrators (protects even repo owners)
   ❌ Allow force pushes (keep disabled)
   ❌ Allow deletions (keep disabled)
   ```

4. **Additional Recommended Settings**
   ```
   ✅ Restrict pushes that create files larger than 100MB
   ✅ Require signed commits (optional but recommended)
   ```

### What This Achieves:

- 🚫 **No direct pushes to main** - All changes must go through PRs
- 👥 **Mandatory code review** - At least 1 approval required
- 🔄 **Auto-dismiss stale reviews** - New commits require fresh approval
- 🛡️ **Even admins protected** - No exceptions for repo owners
- 🚀 **Render safety** - Production can only be updated via reviewed PRs

### Workflow After Setup:

1. **Development**: Work on `web-search` branch
2. **Review**: Create PR from `web-search` → `main`
3. **Approval**: Get review approval (can be self-approved if you're the owner)
4. **Deploy**: Merge PR → Render auto-deploys from `main`

---

**Status**: ⚠️ Manual setup required on GitHub
**Priority**: High (protects production deployment)
**Setup Time**: 2-3 minutes 