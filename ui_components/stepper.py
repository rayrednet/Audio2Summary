def render_stepper(step):
    """Dynamically renders the stepper UI based on the current step using proper HTML rendering"""
    step_titles = [
        "📩 Uploading file...",
        "🔄 Extracting audio...",
        "📝 Transcribing audio...",
        "📑 Summarizing transcript...",
        "📄 Generating PDF...",
    ]

    stepper_html = '<div class="stepper">'
    for i, title in enumerate(step_titles):
        status_class = "inactive"

        if i < step:
            status_class = "completed"  # ✅ Steps that are done become pink
        elif i == step:
            status_class = "active"  # ✅ The current step being processed is highlighted

        # ✅ Apply `final-step` only when progress reaches the last step
        if i <= step:  # Mark all steps up to the current one as completed
            status_class = "completed"

        if i == len(step_titles) - 1 and step == len(step_titles) - 1:
            status_class = "final-step completed"  # Ensure last step gets both classes

        stepper_html += f'''
        <div class="step {status_class}">
            <div class="circle">{i + 1}</div>
            <div>{title}</div>
        </div>
        '''

    stepper_html += '</div>'
    return stepper_html, len(step_titles)