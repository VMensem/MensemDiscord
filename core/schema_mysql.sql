-- Users and Profiles (Unified)
CREATE TABLE IF NOT EXISTS users (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    balance BIGINT DEFAULT 0,
    bank BIGINT DEFAULT 0,
    xp BIGINT DEFAULT 0,
    level INTEGER DEFAULT 1,
    last_xp DOUBLE DEFAULT 0,
    reputation INTEGER DEFAULT 0,
    messages BIGINT DEFAULT 0,
    voice_seconds BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

-- Economy
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    type VARCHAR(50),
    amount BIGINT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shop_items (
    item_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name TEXT NOT NULL,
    price BIGINT NOT NULL,
    type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory (
    inventory_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    item_id BIGINT REFERENCES shop_items(item_id),
    amount INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS cooldowns (
    cooldown_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    command TEXT NOT NULL,
    expires_at TIMESTAMP NULL
);

-- Guild Settings
CREATE TABLE IF NOT EXISTS guild_settings (
    guild_id BIGINT PRIMARY KEY,
    log_channels JSON,
    ticket_category_id BIGINT,
    ticket_log_channel_id BIGINT,
    staff_role_ids JSON,
    embed_color VARCHAR(10),
    economy_settings JSON,
    leveling_settings JSON,
    clan_settings JSON,
    event_settings JSON,
    moderation_settings JSON,
    verify_settings JSON
);

-- Clans
CREATE TABLE IF NOT EXISTS clans (
    clan_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    tag VARCHAR(10) NOT NULL,
    description TEXT,
    leader_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    role_id BIGINT,
    category_id BIGINT,
    chat_channel_id BIGINT,
    voice_channel_id BIGINT,
    balance BIGINT DEFAULT 0,
    level INTEGER DEFAULT 1,
    xp BIGINT DEFAULT 0,
    UNIQUE KEY (name),
    UNIQUE KEY (tag)
);

CREATE TABLE IF NOT EXISTS clan_members (
    clan_id BIGINT REFERENCES clans(clan_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (clan_id, user_id)
);

CREATE TABLE IF NOT EXISTS clan_invites (
    invite_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    clan_id BIGINT REFERENCES clans(clan_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clan_history (
    history_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    clan_id BIGINT REFERENCES clans(clan_id) ON DELETE CASCADE,
    action TEXT,
    user_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clan_wars (
    war_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    clan_one BIGINT REFERENCES clans(clan_id) ON DELETE CASCADE,
    clan_two BIGINT REFERENCES clans(clan_id) ON DELETE CASCADE,
    status VARCHAR(20),
    winner BIGINT REFERENCES clans(clan_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tickets
CREATE TABLE IF NOT EXISTS ticket_panels (
    panel_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT,
    message_id BIGINT,
    title TEXT,
    description TEXT,
    color INTEGER
);

CREATE TABLE IF NOT EXISTS ticket_categories (
    category_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    panel_id BIGINT REFERENCES ticket_panels(panel_id) ON DELETE CASCADE,
    name TEXT,
    description TEXT,
    emoji TEXT,
    target_category_id BIGINT,
    staff_role_id BIGINT
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    category_id BIGINT REFERENCES ticket_categories(category_id),
    status VARCHAR(20) DEFAULT 'open',
    claimed_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP NULL
);

-- Events
CREATE TABLE IF NOT EXISTS events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    creator_id BIGINT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    start_time TIMESTAMP NULL,
    end_time TIMESTAMP NULL,
    max_participants INTEGER,
    reward TEXT,
    game TEXT,
    state VARCHAR(20) DEFAULT 'draft',
    channel_id BIGINT,
    message_id BIGINT
);

CREATE TABLE IF NOT EXISTS event_participants (
    event_id BIGINT REFERENCES events(event_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id, user_id)
);

-- Reports
CREATE TABLE IF NOT EXISTS reports (
    report_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    target_id BIGINT,
    channel_id BIGINT,
    reason TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT '🟡 Open',
    moderator_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report_history (
    history_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    report_id BIGINT REFERENCES reports(report_id) ON DELETE CASCADE,
    action TEXT,
    actor_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Moderation
CREATE TABLE IF NOT EXISTS moderation_cases (
    case_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    mod_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moderation_warnings (
    warning_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    case_id BIGINT REFERENCES moderation_cases(case_id) ON DELETE CASCADE,
    reason TEXT
);

CREATE TABLE IF NOT EXISTS moderation_notes (
    note_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS moderation_case_edits (
    edit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    case_id BIGINT REFERENCES moderation_cases(case_id) ON DELETE CASCADE,
    mod_id BIGINT NOT NULL,
    field TEXT,
    old_val TEXT,
    new_val TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staff
CREATE TABLE IF NOT EXISTS staff_applications (
    application_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    position TEXT NOT NULL,
    answers JSON NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reviewer_id BIGINT,
    rejection_reason TEXT,
    channel_id BIGINT,
    message_id BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP NULL
);

-- Voice
CREATE TABLE IF NOT EXISTS voice_rooms (
    room_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    owner_id BIGINT NOT NULL,
    room_type TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    panel_channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY (channel_id)
);

CREATE TABLE IF NOT EXISTS voice_personal_rooms (
    personal_room_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY (user_id)
);

CREATE TABLE IF NOT EXISTS voice_couples (
    couple_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user1_id BIGINT NOT NULL,
    user2_id BIGINT NOT NULL,
    channel_id BIGINT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Verify Stats
CREATE TABLE IF NOT EXISTS verify_voice_totals (
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    seconds BIGINT DEFAULT 0,
    PRIMARY KEY (guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS verify_support_daily (
    day DATE NOT NULL,
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    seconds BIGINT DEFAULT 0,
    PRIMARY KEY (day, guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS verify_active_voice (
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    joined_at TIMESTAMP NOT NULL,
    PRIMARY KEY (guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS verify_daily_reports (
    day DATE PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS verify_support_actions (
    day DATE NOT NULL,
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    verified INTEGER DEFAULT 0,
    no_access INTEGER DEFAULT 0,
    PRIMARY KEY (day, guild_id, member_id)
);

CREATE TABLE IF NOT EXISTS verify_support_reviews (
    review_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    day DATE NOT NULL,
    guild_id BIGINT NOT NULL,
    member_id BIGINT NOT NULL,
    reviewer_id BIGINT NOT NULL,
    reviewer_name TEXT NOT NULL,
    rating INTEGER NOT NULL,
    comment TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suggestions
CREATE TABLE IF NOT EXISTS suggestions (
    suggestion_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    message_id BIGINT,
    author_id BIGINT NOT NULL,
    channel_id BIGINT,
    title TEXT,
    description TEXT,
    status VARCHAR(50) DEFAULT '🟡 На рассмотрении',
    comment TEXT,
    admin_id BIGINT,
    votes_up JSON,
    votes_down JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS suggestion_config (
    guild_id BIGINT NOT NULL,
    key_name VARCHAR(50) NOT NULL,
    value BIGINT,
    PRIMARY KEY (guild_id, key_name)
);

-- Giveaways
CREATE TABLE IF NOT EXISTS giveaways (
    message_id BIGINT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    prize TEXT NOT NULL,
    winner_count INTEGER DEFAULT 1,
    conditions TEXT,
    creator_id BIGINT NOT NULL,
    end_time TIMESTAMP NOT NULL,
    ended BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS giveaway_participants (
    message_id BIGINT REFERENCES giveaways(message_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    PRIMARY KEY (message_id, user_id)
);

CREATE TABLE IF NOT EXISTS giveaway_winners (
    message_id BIGINT REFERENCES giveaways(message_id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL,
    position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (message_id, user_id)
);

CREATE TABLE IF NOT EXISTS giveaway_rerolls (
    reroll_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    message_id BIGINT REFERENCES giveaways(message_id) ON DELETE CASCADE,
    old_winner_id BIGINT,
    new_winner_id BIGINT,
    performed_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Embed Templates
CREATE TABLE IF NOT EXISTS message_templates (
    template_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    name TEXT NOT NULL,
    json_data JSON NOT NULL
);

-- Reaction Roles
CREATE TABLE IF NOT EXISTS reaction_roles (
    guild_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    emoji VARCHAR(255) NOT NULL,
    role_id BIGINT NOT NULL,
    PRIMARY KEY (guild_id, message_id, emoji)
);

-- AI Assistant
CREATE TABLE IF NOT EXISTS ai_history (
    message_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_ratelimits (
    user_id BIGINT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_config (
    guild_id BIGINT NOT NULL,
    key_name VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (guild_id, key_name)
);

-- AI Knowledge Base
CREATE TABLE IF NOT EXISTS ai_knowledge_base (
    kb_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Anti-Nuke
CREATE TABLE IF NOT EXISTS antinuke_settings (
    guild_id BIGINT PRIMARY KEY,
    enabled BOOLEAN DEFAULT FALSE,
    emergency_mode BOOLEAN DEFAULT FALSE,
    default_action VARCHAR(20) DEFAULT 'alert',
    alert_channel_id BIGINT,
    log_channel_id BIGINT,
    global_threshold INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS antinuke_limits (
    guild_id BIGINT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    max_actions INTEGER NOT NULL,
    window_seconds INTEGER NOT NULL,
    severity VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (guild_id, action_type)
);

CREATE TABLE IF NOT EXISTS antinuke_whitelist (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    added_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS antinuke_trusted (
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    added_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

CREATE TABLE IF NOT EXISTS antinuke_incidents (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    action_count INTEGER NOT NULL,
    action_data JSON,
    action_taken TEXT,
    rollback_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS antinuke_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    object_id BIGINT NOT NULL,
    snapshot_data JSON NOT NULL,
    incident_id BIGINT REFERENCES antinuke_incidents(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_antinuke_incidents_guild_action ON antinuke_incidents(guild_id, action_type);
CREATE INDEX IF NOT EXISTS idx_antinuke_incidents_guild_created ON antinuke_incidents(guild_id, created_at);
CREATE INDEX IF NOT EXISTS idx_antinuke_limits_guild_action ON antinuke_limits(guild_id, action_type);
CREATE INDEX IF NOT EXISTS idx_antinuke_whitelist_guild_user ON antinuke_whitelist(guild_id, user_id);
CREATE INDEX IF NOT EXISTS idx_antinuke_trusted_guild_user ON antinuke_trusted(guild_id, user_id);
