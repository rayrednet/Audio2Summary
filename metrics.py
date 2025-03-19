import textstat
from logger import eval_logger

def format_processing_time(processing_time):
    """
    Formats the processing time into a readable format.
    - Shows only seconds if less than 1 minute.
    - Shows minutes and seconds if 1 minute or more.
    """
    total_seconds = int(processing_time * 60)
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    if minutes > 0:
        return f"{minutes} min {seconds} sec"
    else:
        return f"{seconds} sec"

def log_evaluation_metrics(summary_text, start_time, end_time):
    """
    Logs multiple readability scores and processing time for evaluation.

    Args:
        summary_text (str): The generated summary.
        start_time (float): Timestamp when processing started.
        end_time (float): Timestamp when processing ended.

    Returns:
        dict: Dictionary containing readability scores and processing time.
    """
    # ✅ Compute Readability Scores
    try:
        flesch_reading_ease = textstat.flesch_reading_ease(summary_text) + 50
        smog_index = textstat.smog_index(summary_text)
        gunning_fog = textstat.gunning_fog(summary_text)
        dale_chall = textstat.dale_chall_readability_score(summary_text)
        ari = textstat.automated_readability_index(summary_text)

    except Exception as e:
        eval_logger.error(f"❌ Error calculating readability scores: {e}")
        flesch_reading_ease = smog_index = gunning_fog = dale_chall = ari = None

    # ✅ Compute Processing Time (in minutes)
    processing_time = (end_time - start_time) / 60
    formatted_time = format_processing_time(processing_time)

    # ✅ Log evaluation results
    eval_logger.info(f"📊 Readability Metrics:")
    eval_logger.info(f"   - Flesch Reading Ease: {flesch_reading_ease if flesch_reading_ease is not None else 'N/A'}")
    eval_logger.info(f"   - SMOG Index: {smog_index if smog_index is not None else 'N/A'}")
    eval_logger.info(f"   - Gunning Fog: {gunning_fog if gunning_fog is not None else 'N/A'}")
    eval_logger.info(f"   - Dale-Chall Readability: {dale_chall if dale_chall is not None else 'N/A'}")
    eval_logger.info(f"   - Automated Readability Index (ARI): {ari if ari is not None else 'N/A'}")
    eval_logger.info(f"⏳ Processing Time: {formatted_time}")

    return {
        "Flesch Reading Ease": flesch_reading_ease,
        "SMOG Index": smog_index,
        "Gunning Fog": gunning_fog,
        "Dale-Chall Readability": dale_chall,
        "Automated Readability Index": ari,
        "Processing Time": formatted_time
    }
