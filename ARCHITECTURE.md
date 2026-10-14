# Architecture and implemented scope

Vite/React account UI -> authenticated FastAPI and async SQLAlchemy -> several video pipelines -> provider SDKs, stock assets, TTS, MoviePy/FFmpeg; separate legacy/integration/bulk paths also exist.

Script/image/voice orchestration, emotional camera/transitions/captions, usage tracking, user/admin endpoints, video history, bulk/integration/trends modules. Existence of a module is not proof its complete flow works.

## Modules inspected

- `api_usage_tracker.py`: APIUsage, get_tracker, reset_tracker, get_usage_summary, log_call, log_openai_script, log_openai_tts, log_openai_image, log_openai_search_query, log_pexels_search, log_pexels_download, estimate_cost, summary.
- `cinematic_masterpiece.py`: ColorPalette, CameraMove, Beat, Script, to_rgb_uint8, text_size, multiline_text_bbox, _sanitize_prompt_for_logging, _call_openai_json, generate_cinematic_script, generate_cinematic_prompt, enhance_image_cinematic, _to_9x16_1080x1920, generate_ai_image_enhanced, generate_images_for_beats, synth_tts_openai.
- `cinematic_pipeline.py`: Emotion, CameraMove, Scene, Script, get_ffmpeg_path, to_rgb_uint8, get_audio_duration, lerp, ease_out_cubic, get_camera_for_emotion, generate_script, generate_scene_tts, generate_cinematic_prompt, generate_image, generate_video_search_query, fetch_stock_video.
- `download_bgm.py`: source/module definitions inspected.
- `find_ffmpeg.py`: source/module definitions inspected.
- `fix_admin_auth.py`: fix_admin_auth.
- `server.py`: GenerateRequest, GenerateResponse, health_check, generate_video.
- `stock_videos.py`: StockVideoFetcher, get_stock_video_fetcher, fetch_stock_video, __init__, search_video, _get_best_quality_url, download_video, get_video_for_scene, _extract_keywords.
- `test_openai.py`: source/module definitions inspected.
- `video_effects.py`: crossfade_clips, zoom_transition, create_light_leak_overlay, apply_film_grain, apply_vignette, apply_color_grade, apply_shake, apply_pulse_zoom, apply_all_effects, create_animated_light_leak_clip, create_particle_overlay, zoom_out_frame.
- `web_app/eslint.config.js`: source/module definitions inspected.
- `web_app/postcss.config.js`: source/module definitions inspected.
- `web_app/tailwind.config.js`: source/module definitions inspected.
- `web_app/vite.config.js`: source/module definitions inspected.
- `web_app/src/App.jsx`: FloatingParticles, AnimatedOrbs, SimpleLogo, App, handleMouseMove, handleGenerate, handleTrendSelect, handleLogout, formatTime.
- `web_app/src/main.jsx`: ProtectedRoute, AdminRoute, PublicRoute, AppRoutes.
- `web_app/src/services/api.js`: getToken, setToken, getStoredUser, setStoredUser, authFetch.
- `web_app/src/pages/AdminDashboard.jsx`: AdminDashboard, loadData, loadUserDetails.
- `web_app/src/pages/LoginPage.jsx`: LoginPage, handleSubmit.
- `web_app/src/pages/SignupPage.jsx`: SignupPage, handleSubmit.
- `web_app/src/hooks/useVideoGeneration.js`: useVideoGeneration.
- `web_app/src/context/AuthContext.jsx`: AuthProvider, checkAuth, login, signup, logout, refreshUserInfo, useAuth.
- `web_app/src/components/GenerateButton.jsx`: GenerateButton.
- `web_app/src/components/Header.jsx`: Header.
- `web_app/src/components/ProgressBar.jsx`: ProgressBar.
- `web_app/src/components/PromptInput.jsx`: PromptInput.
- `web_app/src/components/Selectors.jsx`: OptionSelector, LanguageSelector, DurationSelector, StyleSelector, VoiceSelector.
- `web_app/src/components/StatusMessage.jsx`: StatusMessage.
- `web_app/src/components/TrendWidget.jsx`: TrendWidget, fetchTrends.
- `web_app/src/components/VideoPreview.jsx`: VideoPreview.
- `video_engine/assets.py`: AssetManager, __init__, generate_dalle_image, download_file.
- `video_engine/audio.py`: AudioManager, __init__, generate_tts, _convert_to_wav, mix_audio.
- `video_engine/editor.py`: VideoEditor, __init__, create_clip, _animate_image, _resize_to_vertical, _create_text_overlay, _create_watermark_overlay, assemble_video.
- `video_engine/engine.py`: VideoEngine, __init__, generate_video, process_scene_assets.
- `video_engine/scripting.py`: Language, ScriptBeat, VideoScript, ScriptGenerator, __init__, generate_script.
- `video_engine/transitions.py`: Emotion, TransitionType, TransitionConfig, TransitionDecision, SmartTransitions, get_smart_transition, get_all_transitions, __init__, analyze_emotional_shift, select_transition, get_transition_sequence, apply_transition, apply_transition_with_sound, slide_out, slide_in.
- `video_engine/__init__.py`: source/module definitions inspected.
- `core/engine.py`: Beat, VideoEngine, __init__, generate_video, _align_beats, _generate_images, _compose_video, make_frame.
- `core/models.py`: Language, CameraMove, Emotion, ColorPalette, ScriptBeat, VideoScript, GenerationContext.
- `core/__init__.py`: source/module definitions inspected.
- `core/utils/compatibility.py`: text_size, multiline_text_bbox, to_rgb_uint8, setup_console_encoding.
- `core/utils/helpers.py`: sanitize_filename, format_srt_timestamp, estimate_duration, lerp, ease_in_cubic, ease_out_cubic, ease_out_expo, ease_in_out_cubic, clamp, find_ffmpeg.
- `core/utils/__init__.py`: source/module definitions inspected.
- `core/services/trend_monitor.py`: ContentNiche, TrendingTopic, AutoGeneratedVideo, TrendJackEngine, get_trending_now, generate_trend_videos, __init__, _init_reddit, get_trending_topics, _get_reddit_trends, _get_hackernews_trends, _get_google_trends, _get_mock_reddit_trends, _score_trends, _suggest_angle, auto_generate_daily_videos.
- `core/services/__init__.py`: source/module definitions inspected.
- `core/optimization/ab_testing.py`: VariantType, VariantConfig, GeneratedVariant, ABTestResult, VideoVariantGenerator, generate_ab_test, get_variant_templates, __init__, _generate_hook, _predict_variant_score, generate_single_variant, generate_variants, _generate_recommendation_reason, get_comparison_report, create_custom_variant.
- `core/optimization/__init__.py`: source/module definitions inspected.
- `core/generators/audio.py`: AudioGenerator, __init__, generate_tts, _convert_to_wav, get_duration, transcribe, mix_audio, normalize_loudness.
- `core/generators/music_selector.py`: MusicMood, MusicSelector, __init__, _scan_library, select, get_mood_from_emotions.
- `core/generators/visual.py`: VisualGenerator, __init__, generate, _resize_to_vertical, _enhance_cinematic, _apply_teal_orange_grade, _create_placeholder, generate_batch.
- `core/generators/__init__.py`: source/module definitions inspected.
- `core/effects/camera.py`: get_movement_params, apply_camera_movement, apply_camera_to_frame.
- `core/effects/captions.py`: load_font, create_cinematic_caption, create_title_card.
- `core/effects/grading.py`: get_grading_params, grade_image_by_emotion, apply_lut, add_film_grain, add_vignette.
- `core/effects/overlays.py`: OverlayManager, create_letterbox, create_lens_flare, create_light_leak, create_animated_grain, create_bokeh_overlay, __init__, get_letterbox, get_lens_flare, get_light_leak, get_grain, get_bokeh, composite_overlay.
- `core/effects/particles.py`: create_particles_overlay, create_dust_overlay, create_light_leak, create_bokeh_overlay, make_frame, make_frame, make_frame, make_frame.
- `core/effects/transitions.py`: TransitionManager, crossfade_transition, zoom_transition, wipe_transition, light_wipe_transition, push_transition, __init__, get_transition, apply_transition, suggest_transition.
- `core/effects/__init__.py`: source/module definitions inspected.
- `core/analytics/hook_scorer.py`: HookPattern, HookScore, SceneData, ViralHookAnalyzer, analyze_hook, get_hook_score, is_viral_hook, __init__, analyze_hook, _detect_bright_colors, _calculate_grade, _calculate_viral_potential, _generate_suggestions, analyze_script_hooks, generate_improved_hook.
- `core/analytics/__init__.py`: source/module definitions inspected.
- `core/ai/cinematographer.py`: ShotPlan, Cinematographer, __init__, plan_shot, _get_movement_params, _alternate_move, _analyze_shot_type, apply_movement, plan_sequence, get_transition_recommendation.
- `core/ai/director.py`: PacingStyle, CameraStyle, ColorMood, PacingDecision, ColorDecision, CameraDecision, MusicCue, EmotionalBeat, DirectorVision, AIDirector, direct_video, __init__, analyze_script, _detect_dominant_emotion, _decide_pacing, _decide_colors, _suggest_lut, _plan_camera_movements, _create_music_map, _map_emotional_arc, _suggest_visual_metaphors, _determine_overall_style.
- `core/ai/emotion_mapper.py`: StyleConfig, EmotionMapper, __init__, get_style, get_palette, get_palette_colors, enhance_visual_prompt, get_grading_params, suggest_camera_move, get_music_style, get_pacing, get_transition, blend_emotions.
- `core/ai/model_router.py`: AIProvider, ModelConfig, RoutingDecision, IntelligentModelRouter, ModelClient, get_router, get_model_client, smart_complete, __init__, _detect_available_providers, _is_provider_available, _get_model_config, _estimate_cost, _get_budget_tier, route, _track_usage, get_usage_report.
- `core/ai/prompt_interpreter.py`: PromptInterpreter, __init__, interpret, refine_script.
- `core/ai/__init__.py`: source/module definitions inspected.
- `backend/config.py`: Settings, Config, get_settings.
- `backend/database.py`: Base, get_db, init_db.
- `backend/deps.py`: verify_password, get_password_hash, create_access_token, get_current_user, get_current_admin, check_rate_limit, get_user_video_count_today.
- `backend/main.py`: create_admin_if_not_exists, create_asset_directories, lifespan, root.
- `backend/models.py`: User, VideoGeneration, __repr__, __repr__.
- `backend/__init__.py`: source/module definitions inspected.
- `backend/services/caption_engine.py`: TimedWord, CaptionEngine, get_available_styles, create_caption_engine, duration, __init__, estimate_word_timing, create_caption_clip, create_sentence_captions, create_word_by_word_captions, add_captions_to_video.
- `backend/services/music_service.py`: MusicService, get_music_service, __init__, _scan_music_library, detect_mood, get_track, get_volume_for_content, get_all_moods, add_track.
- `backend/services/stock_service.py`: StockVideo, StockVideoService, create_stock_service, is_vertical, __init__, search, download, extract_keywords, get_video_for_scene.
- `backend/services/__init__.py`: source/module definitions inspected.
- `backend/routes/admin.py`: UserSummary, VideoSummary, AnalyticsResponse, get_analytics, list_users, list_videos, get_user_details.
- `backend/routes/auth.py`: SignupRequest, LoginRequest, TokenResponse, UserResponse, signup, login, get_me.
- `backend/routes/bulk.py`: BulkJobStatus, BulkGenerateResponse, VideoRow, generate_bulk_job_id, parse_csv, process_bulk_job, bulk_generate, get_bulk_status, list_bulk_jobs, cancel_bulk_job, get_csv_template, download_csv_template.
- `backend/routes/generate.py`: MagicGenerateRequest, MagicGenerateResponse, SceneSpec, GenerateRequest, GenerateResponse, JobStatus, auto_select_parameters, run_pipeline_task, magic_generate, generate_video, get_job_status, get_my_videos, list_styles, list_voices, list_languages, update_progress, update_db, update_db_failed.
- `backend/routes/health.py`: health_check.
- `backend/routes/integrations.py`: ZapierGenerateRequest, ZapierGenerateResponse, JobStatusResponse, WebhookSubscribeRequest, WebhookSubscription, generate_job_id, sign_webhook_payload, send_webhook, process_video_generation, zapier_generate_video, get_job_status, subscribe_webhook, unsubscribe_webhook, test_webhook, zapier_auth_test, zapier_list_triggers, zapier_list_actions.
- `backend/routes/trends.py`: TrendResponse, TrendsListResponse, GenerateFromTrendRequest, AutoGenerateRequest, ReadyVideoResponse, get_trending_now, generate_from_trend, auto_generate_daily, get_ready_videos, list_available_niches, _generate_trend_video, _auto_generate_batch, _get_status_message.
- `backend/routes/__init__.py`: source/module definitions inspected.

## Request routes

| Source | Method | Path | Handler |
|---|---|---|---|
| `server.py` | get | `/` | `health_check` |
| `server.py` | post | `/generate` | `generate_video` |
| `backend/main.py` | get | `/` | `root` |
| `backend/routes/admin.py` | get | `/analytics` | `get_analytics` |
| `backend/routes/admin.py` | get | `/users` | `list_users` |
| `backend/routes/admin.py` | get | `/videos` | `list_videos` |
| `backend/routes/admin.py` | get | `/user/{user_id}` | `get_user_details` |
| `backend/routes/auth.py` | post | `/signup` | `signup` |
| `backend/routes/auth.py` | post | `/login` | `login` |
| `backend/routes/auth.py` | get | `/me` | `get_me` |
| `backend/routes/bulk.py` | post | `/generate` | `bulk_generate` |
| `backend/routes/bulk.py` | get | `/status/{job_id}` | `get_bulk_status` |
| `backend/routes/bulk.py` | get | `/jobs` | `list_bulk_jobs` |
| `backend/routes/bulk.py` | delete | `/{job_id}` | `cancel_bulk_job` |
| `backend/routes/bulk.py` | get | `/template` | `get_csv_template` |
| `backend/routes/bulk.py` | get | `/template.csv` | `download_csv_template` |
| `backend/routes/generate.py` | post | `/magic` | `magic_generate` |
| `backend/routes/generate.py` | post | `/generate` | `generate_video` |
| `backend/routes/generate.py` | get | `/generate/{job_id}` | `get_job_status` |
| `backend/routes/generate.py` | get | `/my-videos` | `get_my_videos` |
| `backend/routes/generate.py` | get | `/styles` | `list_styles` |
| `backend/routes/generate.py` | get | `/voices` | `list_voices` |
| `backend/routes/generate.py` | get | `/languages` | `list_languages` |
| `backend/routes/health.py` | get | `/health` | `health_check` |
| `backend/routes/integrations.py` | post | `/zapier/generate` | `zapier_generate_video` |
| `backend/routes/integrations.py` | get | `/zapier/status/{job_id}` | `get_job_status` |
| `backend/routes/integrations.py` | post | `/webhook/subscribe` | `subscribe_webhook` |
| `backend/routes/integrations.py` | delete | `/webhook/{subscription_id}` | `unsubscribe_webhook` |
| `backend/routes/integrations.py` | get | `/webhook/test/{subscription_id}` | `test_webhook` |
| `backend/routes/integrations.py` | get | `/zapier/auth/test` | `zapier_auth_test` |
| `backend/routes/integrations.py` | get | `/zapier/triggers` | `zapier_list_triggers` |
| `backend/routes/integrations.py` | get | `/zapier/actions` | `zapier_list_actions` |
| `backend/routes/integrations.py` | post | `/make/generate` | `make_generate_video` |
| `backend/routes/integrations.py` | post | `/webhook/receive` | `receive_webhook` |
| `backend/routes/trends.py` | get | `/now` | `get_trending_now` |
| `backend/routes/trends.py` | post | `/generate` | `generate_from_trend` |
| `backend/routes/trends.py` | post | `/auto-generate` | `auto_generate_daily` |
| `backend/routes/trends.py` | get | `/ready/{batch_id}` | `get_ready_videos` |
| `backend/routes/trends.py` | get | `/niches` | `list_available_niches` |

Static parsing found the modules/handlers above without importing/executing them. Fixtures, enums and abstract declarations are not proof that every flow is complete. See TECHNICAL_ISSUES.md for incomplete adapters and inconsistent pipeline contracts.
