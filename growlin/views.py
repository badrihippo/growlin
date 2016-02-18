from flask import Flask, render_template, redirect, abort, flash, request, url_for, current_app, session
from .app import app
from .auth import current_user, login_required
from .models import *
from .forms import *

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('user_shelf'))
    else:
	return redirect(url_for('login'))

@app.route('/user/<username>/')
def user(username):
    return render_template('base.htm', username=username)

@app.route('/shelf/')
@login_required
def user_shelf():
    records = current_user.get_current_borrowings()
    return render_template('user/shelf.htm', records=records)

@app.route('/shelf/history/')
@login_required
def user_history():
    records = current_user.get_past_borrowings()
    return render_template('shelf/history.htm', records=records)

@app.route('/shelf/borrow/', methods=['GET', 'POST'])
def user_borrow():
    cform = AccessionItemForm()
    form = AccessionForm()
    if cform.validate_on_submit():
        # Accession number entered and confirmed
        acc = cform.accession.data
        # Check for item exists
        try:
            item = Item.objects.get(accession=acc)
        except Item.DoesNotExist:
            return render_template('user/borrow.htm',
                error='This book does not exist. Please check the number and try again.',
                form = form)
        try:
            current_user.borrow(item, acc)
            flash('"%s" has been added to your shelf.' % item.title)
            return redirect(url_for('user_shelf'))
        except BorrowError, e:
            return render_template('user/borrow.htm',
            error=e.message,
            form = form)
    elif form.validate_on_submit():
        # Accession entered but needs to be confirmed
        # Using new AccessionItemForm instead of validation-failed one
        cform = AccessionItemForm()
        a = form.accession.data

        # Check for item exists
        try:
            item = Item.objects.get(accession=a)
        except Item.DoesNotExist:
            return render_template('user/borrow.htm',
                error='This book does not exist. Please check the number and try again.',
                form = form)

        # Check for already borrowed
        b = item.borrow_current
        if b and b is not None:
            error = 'That item is already borrowed by %(name)s (%(group)s)!' % {
                'name': b.user.name,
                'group': b.user.user_group
                }
            return render_template('user/borrow.htm',
                error=error,
                form = form)
        else:
            #Not borrowed so it's okay
            # Show confirmation form
            cform.item = item.id
            cform.accession = form.accession.data
            return render_template('user/borrow.htm',
                form=cform, item=item)
    else:
        return render_template('user/borrow.htm', form=form)

@app.route('/shelf/<borrowid>/return/', methods=['GET', 'POST'] )
@login_required
def user_return(borrowid):
    try:
        item = Item.objects.get(id=borrowid)
    except Item.DoesNotExist:
        flash('Please decide what you want to return')
        return redirect(url_for('user_shelf'))
    form = AccessionForm()
    if form.validate_on_submit():
        try:
            current_user.unborrow(item, form.accession.data)
            flash('"%(title)s" has been successfully returned' % {
                'title': item.title})
        except BorrowError, e:
            flash(e.message)
    else:
        if item.borrow_current.user.id == current_user.id:
            msg = 'Please enter the accession number for "%(title)s"' % {
                'title': item.title}
            return render_template('shelf/accession_entry.htm',
                message=msg,
                form=form,
                item=item,
                sumbit_button_text='Return')
        else:
            flash('That item was borrowed by %(name)s, not by you!' % {
                'name': item.borrow_current.user.name})
    return redirect(url_for('user_shelf'))
