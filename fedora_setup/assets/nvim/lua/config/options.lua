local opt = vim.opt

-- Appearance
opt.number         = true
opt.relativenumber = true
opt.cursorline     = true
opt.signcolumn     = "yes"
opt.termguicolors  = true
opt.showmode       = false
opt.laststatus     = 3
opt.pumheight      = 10
opt.conceallevel   = 1
opt.scrolloff      = 10
opt.sidescrolloff  = 8
opt.wrap           = false

-- Indentation
opt.tabstop     = 2
opt.shiftwidth  = 2
opt.expandtab   = true
opt.smartindent = true
opt.shiftround  = true

-- Search
opt.ignorecase = true
opt.smartcase  = true
opt.hlsearch   = true

-- Splits
opt.splitright = true
opt.splitbelow = true

-- Files
opt.undofile   = true
opt.swapfile   = false
opt.backup     = false
opt.updatetime = 250
opt.timeoutlen = 300

-- Clipboard & mouse
opt.clipboard  = "unnamedplus"
opt.mouse      = "a"

-- Completion
opt.completeopt = "menu,menuone,noselect"

-- Folding (treesitter-based, disabled by default — open with zR)
opt.foldmethod  = "expr"
opt.foldexpr    = "v:lua.vim.treesitter.foldexpr()"
opt.foldenable  = false

-- Don't auto-insert comment leaders on o/O or Enter
opt.formatoptions:remove({ "c", "r", "o" })
